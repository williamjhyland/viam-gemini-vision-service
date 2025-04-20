import traceback
from typing import ClassVar, List, Mapping, Optional, Sequence, Any, cast

from google import genai
from google.genai.types import HttpOptions, Part, Content  # Import Content

from viam.logging import getLogger
from viam.media.video import ViamImage
from viam.proto.app.robot import ComponentConfig
from viam.proto.common import ResourceName
from viam.proto.service.vision import Classification
from viam.resource.base import ResourceBase
from viam.resource.easy_resource import EasyResource
from viam.resource.types import Model, ModelFamily
from viam.components.camera import Camera
from viam.services.vision import CaptureAllResult, Vision as ViamVisionService
from viam.utils import struct_to_dict, ValueTypes, from_dm_from_extra
from viam.errors import NoCaptureToStoreError

LOGGER = getLogger(__name__)

class Vision(ViamVisionService, EasyResource):
    MODEL: ClassVar[Model] = Model(ModelFamily("bill", "gemini"), "vision")

    @classmethod
    def validate_config(cls, config: ComponentConfig) -> Sequence[str]:
        for key in ("model_id", "api_key", "camera_name"):
            if key not in config.attributes.fields:
                raise ValueError(f"Missing Vision config attribute '{key}'")
        return []

    def reconfigure(
        self, config: ComponentConfig, deps: Mapping[ResourceName, ResourceBase]
    ):
        LOGGER.info(f"[{self.name}] reconfigure called")
        cfg = struct_to_dict(config.attributes)
        self.api_key     = cfg["api_key"]
        self.model_id    = cfg["model_id"]
        self.camera_name = cfg["camera_name"]
        self._deps       = deps

        self.client = genai.Client(
            api_key=self.api_key,
            http_options=HttpOptions(api_version="v1"),
        )
        LOGGER.info(f"[{self.name}] Gemini client initialized")

    async def _gemini(self, parts: List[Content], **kwargs) -> str:  # Use List[Content]
        try:
            resp = self.client.models.generate_content(
                model=self.model_id, contents=parts, **kwargs
            )
            text = resp.text.strip()
            LOGGER.debug(
                f"[{self.name}] Gemini raw → {text[:120]}{'...' if len(text)>120 else ''}"
            )
            return text
        except Exception:
            LOGGER.error(f"[{self.name}] Gemini call failed\n{traceback.format_exc()}")
            raise

    async def get_classifications(
        self, image: ViamImage, count: int, **_
    ) -> List[Classification]:
        image_part = Part.from_data(data=image.data, mime_type="image/jpeg")
        prompt = "Describe this image in one concise English sentence."
        contents = [
            Content(parts=[image_part]),  # Wrap image_part in Content
            Content(parts=[Content.Part(text=prompt)])  # Wrap prompt in Content.Part
        ]

        description = await self._gemini(contents)
        return [Classification(label=description, confidence=1.0)]

    async def capture_all_from_camera(
        self,
        camera_name: str,
        return_image: bool = False,
        return_classifications: bool = False,
        return_detections: bool = False,
        return_object_point_clouds: bool = False,
        *,
        extra: Optional[Mapping[str, Any]] = None,
        timeout: Optional[float] = None,
    ) -> CaptureAllResult:
        result = CaptureAllResult()

        # 1. grab a frame
        cam_rn = Camera.get_resource_name(camera_name)
        camera = cast(Camera, self._deps[cam_rn])
        frame  = await camera.get_image(mime_type="image/jpeg")
        if return_image:
            result.image = frame

        # 2. generate a caption as a “classification”
        result.classifications = await self.get_classifications(frame, 1)
        if not return_classifications:
            result.classifications.clear()

        # 3. stubs for detections / point clouds
        result.detections = [] if return_detections else []
        result.objects    = [] if return_object_point_clouds else []

        # 4. Data‑Manager gating
        if from_dm_from_extra(extra):
            if not any(c.label for c in result.classifications):
                raise NoCaptureToStoreError

        return result

    async def get_properties(
        self,
        *,
        extra: Optional[Mapping[str, ValueTypes]] = None,
        timeout: Optional[float] = None,
    ) -> ViamVisionService.Properties:
        return ViamVisionService.Properties()

    # fallbacks for the other RPCs
    async def get_classifications_from_camera(self, cam: str, count: int, **kw):
        frame = await self.capture_all_from_camera(
            cam, return_image=True, return_classifications=True
        )
        return frame.classifications

    async def get_description_from_camera(self, cam: str, prompt: str, **kw):
        frame = await self.capture_all_from_camera(cam, return_image=True)
        return await self.get_description(frame.image, prompt, **kw)

    async def get_description(self, image: ViamImage, prompt: str, **kw):
        image_part = Part.from_data(data=image.data, mime_type="image/jpeg")
        contents = [
            Content(parts=[image_part]),
            Content(parts=[Content.Part(text=prompt)]) # Wrap prompt in Content.Part
        ]
        return await self._gemini(contents)

    async def get_detections_from_camera(self, *a, **k):
        raise NotImplementedError()

    async def get_detections(self, *a, **k):
        raise NotImplementedError()

    async def get_object_point_clouds(self, *a, **k):
        raise NotImplementedError()

    async def do_command(self, *a, **k):
        raise NotImplementedError()