# Module gemini

This module provides a vision service that leverages Google's Gemini multimodal LLM to generate natural language descriptions of camera images in real-time.

## Model bill:gemini:vision

A Viam vision service that captures images from a camera, processes them through Google's Gemini API, and returns detailed text descriptions of what the AI sees.

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

The following attributes are available for this model:

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

### DoCommand

This model does not currently implement DoCommand functionality.