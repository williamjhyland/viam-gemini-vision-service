# Module gemini

This module provides a vision service that integrates Google's Gemini multimodal LLM with Viam's platform to generate natural language descriptions of camera images in real-time.

## Model bill:gemini:vision

A Viam vision service that captures images from a camera, processes them through Google's Gemini API, and returns detailed text descriptions of what the AI sees.

**Core Features:**
- Captures images from any Viam-compatible camera
- Processes images through Google's Gemini models
- Returns concise natural language descriptions of visual content
- Implements standard Viam Vision service interfaces

### Prerequisites

- A Viam account with a registered machine
- A Google AI Studio account with API access
- A Gemini API key

### Configuration

The following attribute template can be used to configure this model:

```json
{
  "api_key": <string>,
  "camera_name": <string>,
  "model": <string>,
  "prompt": <string>,
  "system_instruction": "<string>",
  "temperature": <float>,
  "top_p": <float>,
  "max_output_tokens": <integer>,
  "safety_settings": [
    {
      "category": "<string>",
      "threshold": "<string>"
    }
  ]
}
```

#### Attributes

| Name          | Type   | Inclusion | Description                                         |
|---------------|--------|-----------|-----------------------------------------------------|
| `api_key`     | string | Required  | Your Google Gemini API key                          |
| `camera_name` | string | Required  | Resource name of the camera to capture images from  |
| `model`       | string | Required  | Gemini model to use (e.g., "gemini-2.5-flash")      |
| `prompt`      | string | Required  | Text prompt to send with each image                 |
| `system_instruction`      | string | Optional  | System-level instruction to guide model behavior across all interactions                 |
| `temperature`      | float | Optional  | Controls randomness in generation (0.0-2.0) lower = more deterministic, higher = more creative                 |
| `top_p`      | float | Optional  | Nucleus sampling threshold (0.0-1.0) controls diversity of word selection                 |
| `max_output_tokens`      | integer | Optional  | Maximum number of tokens in the model's response |
| `safety_settings`      | array | Optional  | List of safety settings to control content filtering per category |

#### Example Configuration (Basic)

```json
{
  "api_key": "YOUR_GEMINI_API_KEY",
  "camera_name": "my-camera",
  "model": "gemini-2.0-flash",
  "prompt": "Describe what you see in this image"
}
```

#### Example Configuration (Advanced)

```json
{
  "api_key": "YOUR_GEMINI_API_KEY",
  "camera_name": "my-camera",
  "model": "gemini-2.5-flash",
  "prompt": "What number do you see written on the whiteboard?",
  "system_instruction": "You are a precise OCR assistant. Respond with only the number you see, no additional text.",
  "temperature": 0.1,
  "top_p": 0.95,
  "max_output_tokens": 50,
  "safety_settings": [
    {
      "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
      "threshold": "BLOCK_NONE"
    }
  ]
}
```

### Usage

Once configured, you can use the service through the Viam SDK:

```python
from viam.services.vision import VisionClient
from viam.robot.client import RobotClient

# Connect to your robot
robot = await RobotClient.at_address(
    "ROBOT_ADDRESS",
    Credentials(type="robot", payload="ROBOT_API_KEY"),
)

# Get the vision service
vision = VisionClient.from_robot(robot, "my-gemini-vision")

# Get an image description
result = await vision.capture_all_from_camera(
    "my-camera",
    return_classifications=True
)

# Print the classification (description)
for classification in result.classifications:
    print(f"Description: {classification.class_name}")
```

### Configuration Tips

**System Instructions:**
- Use `system_instruction` to set consistent behavior across all image analyses
- Examples: "Always respond in Spanish", "Focus only on detecting safety hazards", "Provide detailed technical descriptions"

**Temperature:**
- Use low values (0.0-0.5) for consistent, deterministic outputs (e.g., reading numbers, detecting specific objects)
- Use higher values (0.7-2.0) for creative descriptions or varied responses

**Safety Settings:**
- The default safety settings may block legitimate content in some use cases
- Set thresholds to `BLOCK_NONE` only if you're certain your application requires it
- Consider your use case carefully before disabling safety filters

### Example Use Cases

- **Visual alerts**: Generate notifications when specific objects or conditions are detected
- **Data collection**: Log descriptions of environments for later analysis
- **Accessibility**: Convert visual information into text for audio output
- **Autonomous decision-making**: Use scene descriptions to inform robot behaviors

### Limitations

- Image processing happens remotely through Google's API, requiring internet connectivity
- Response times depend on network conditions and Google API response times
- Gemini models may have their own limitations in accurately describing certain scenes
- Safety settings may block legitimate content if configured too strictly

### DoCommand

This model does not currently implement DoCommand functionality.

### Future Extensions

Planned future capabilities:
- Support for object detection (currently stubbed)
- Filtering or categorization of detected objects