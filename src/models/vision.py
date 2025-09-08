import traceback
from typing import ClassVar, List, Mapping, Optional, Sequence, Any, cast

# Google Gemini client and helper types
from google import genai
from google.genai.types import HttpOptions, Part, Content

# For converting raw bytes into a PIL Image
from io import BytesIO
from PIL import Image

# Viam framework imports
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

# Set up a module‐wide logger
LOGGER = getLogger(__name__)

class Vision(ViamVisionService, EasyResource):
    # Define the “model name” under which this service will register
    MODEL: ClassVar[Model] = Model(ModelFamily("bill", "gemini"), "vision")

    @classmethod
    def validate_config(cls, config: ComponentConfig) -> Sequence[str]:
        """
        1. Ensure the config has all required fields:
           - api_key:  your Gemini API key
           - camera_name:  the name of the camera resource to grab frames from
           - model:  which Gemini model to call (e.g. "gemini-2.0-flash")
           - prompt: the text prompt to send alongside each image
        2. Declare a dependency on that camera resource so Viam will wire it up.
        """
        deps = []
        fields = config.attributes.fields

        # Check required attributes
        for key in ("api_key", "camera_name", "model", "prompt"):
            if key not in fields:
                raise ValueError(f"Missing Vision config attribute '{key}'")

        # Record the camera_name as a dependency
        camera_name = fields["camera_name"].string_value
        deps.append(camera_name)

        return deps

    def reconfigure(
        self,
        config: ComponentConfig,
        deps: Mapping[ResourceName, ResourceBase]
    ):
        """
        Called whenever the service is created or its config changes.
        - parse out our attributes
        - stash the camera dependency mapping
        - initialize the Gemini client
        """
        LOGGER.info(f"[{self.name}] reconfigure called")
        cfg = struct_to_dict(config.attributes)

        # Required config params
        self.api_key     = cfg["api_key"]
        self.camera_name = cfg["camera_name"]
        self.model       = cfg["model"]    # e.g. "gemini-2.0-flash"
        self.prompt      = cfg["prompt"]   # e.g. "Describe this image…"
        self._deps       = deps            # mapping of dependencies

        # Instantiate the Gemini client
        self.client = genai.Client(
            api_key=self.api_key,
            http_options=HttpOptions(api_version="v1"),
        )
        LOGGER.info(f"[{self.name}] Gemini client initialized")

    async def _gemini(self, parts: List[Part], **kwargs) -> str:
        """
        Helper that calls the async Gemini endpoint so we don’t block
        Viam’s event loop. Returns the stripped text result.
        """
        resp = await self.client.aio.models.generate_content(
            model=self.model,
            contents=parts,
            **kwargs,
        )
        text = resp.text.strip()
        LOGGER.debug(f"[{self.name}] Gemini → {text!r}")
        return text

    async def get_classifications(
        self,
        image: ViamImage,
        count: int,
        **_
    ) -> List[Classification]:
        """
        Implements the classification RPC:
        1. Load the JPEG bytes into PIL
        2. Call Gemini (blocking client here, but you could switch to self.client.aio)
        3. Wrap the response in a single Classification object
        """
        classifications: List[Classification] = []

        # Convert ViamImage.data bytes → PIL Image
        buf = BytesIO(image.data)
        pil_img = Image.open(buf)

        # Send image + prompt to Gemini
        response = self.client.models.generate_content(
            model=self.model,
            contents=[
                pil_img,
                self.prompt,
            ],
        )
        description = response.text.strip()
        LOGGER.debug(f"[{self.name}] Gemini classification → {description}")

        # Build and return a list of Classification messages
        classification = Classification(confidence=1.0, class_name=description)
        classifications.append(classification)
        return classifications

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
        """
        Canonical ‘capture’ call:
        1. Resolve the named camera dependency
        2. Grab a JPEG frame
        3. Run our classification
        4. Package everything into CaptureAllResult
        """
        result = CaptureAllResult()

        # 1. find the camera resource
        cam_rn = Camera.get_resource_name(camera_name)
        camera = cast(Camera, self._deps[cam_rn])

        # 2. fetch an image
        frame = await camera.get_image(mime_type="image/jpeg")
        result.image = frame

        # 3. classify it
        result.classifications = await self.get_classifications(frame, 1)

        return result

    async def get_properties(
        self,
        *,
        extra: Optional[Mapping[str, ValueTypes]] = None,
        timeout: Optional[float] = None,
    ) -> ViamVisionService.Properties:
        """
        Return any service‐level properties (none for us).
        """
        return ViamVisionService.Properties()

    # Fallback RPCs that delegate to our main methods

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
        # Wrap prompt in a Content.Part for consistency
        contents = [
            Content(parts=[image_part]),
            Content(parts=[Content.Part(text=prompt)]),
        ]
        return await self._gemini(contents)

    # Unimplemented stubs for other RPCs
    async def get_detections_from_camera(self, *a, **k):
        raise NotImplementedError()

    async def get_detections(self, *a, **k):
        raise NotImplementedError()

    async def get_object_point_clouds(self, *a, **k):
        raise NotImplementedError()

    async def do_command(self, *a, **k):
        raise NotImplementedError()
