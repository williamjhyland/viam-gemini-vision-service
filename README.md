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
  "prompt": <string>
}
```

#### Attributes

| Name          | Type   | Inclusion | Description                                         |
|---------------|--------|-----------|-----------------------------------------------------|
| `api_key`     | string | Required  | Your Google Gemini API key                          |
| `camera_name` | string | Required  | Resource name of the camera to capture images from  |
| `model`       | string | Required  | Gemini model to use (e.g., "gemini-2.0-flash")      |
| `prompt`      | string | Required  | Text prompt to send with each image                 |

#### Example Configuration

```json
{
  "api_key": "YOUR_GEMINI_API_KEY",
  "camera_name": "my-camera",
  "model": "gemini-2.0-flash",
  "prompt": "Describe what you see in this image"
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

### Example Use Cases

- **Visual alerts**: Generate notifications when specific objects or conditions are detected
- **Data collection**: Log descriptions of environments for later analysis
- **Accessibility**: Convert visual information into text for audio output
- **Autonomous decision-making**: Use scene descriptions to inform robot behaviors

### Limitations

- Image processing happens remotely through Google's API, requiring internet connectivity
- Response times depend on network conditions and Google API response times
- Gemini models may have their own limitations in accurately describing certain scenes

### DoCommand

This model does not currently implement DoCommand functionality.

### Future Extensions

Planned future capabilities:
- Support for object detection (currently stubbed)
- Filtering or categorization of detected objects