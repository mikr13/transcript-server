# YouTube Transcript API Server

A FastAPI-based server that provides an API for fetching YouTube transcript data using the `youtube-transcript-api` library.

## Features

- 🎯 **Simple API**: Get YouTube transcripts with a single HTTP request
- 📝 **Raw Data Format**: Returns transcript data with text, start time, and duration
- 🌍 **Multi-language Support**: Handles different transcript languages
- 🔧 **Error Handling**: Comprehensive error handling for various edge cases
- 📚 **Auto Documentation**: Interactive API docs via FastAPI
- ⚡ **Modern Stack**: Built with FastAPI and managed with uv

## Installation

This project uses [uv](https://docs.astral.sh/uv/) for dependency management. Make sure you have uv installed:

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Clone and set up the project:

```bash
git clone <repository-url>
cd transcript-server
uv sync  # Install dependencies
```

## Usage

### Starting the Server

```bash
uv run main.py
```

The server will start on `http://localhost:8000`

### API Endpoints

#### Get Transcript

```http
GET /transcript/{video_id}
```

Fetch the transcript for a YouTube video by its ID.

**Example:**

```bash
curl http://localhost:8000/transcript/dQw4w9WgXcQ
```

**Response:**

```json
[
    {
        "text": "Hey there",
        "start": 0.0,
        "duration": 1.54
    },
    {
        "text": "how are you",
        "start": 1.54,
        "duration": 4.16
    }
]
```

#### Batch Transcript Request

```http
POST /transcript/batch
```

Fetch transcripts for multiple YouTube videos in a single request.

**Example:**

```bash
curl -X POST http://localhost:8000/transcript/batch \
  -H "Content-Type: application/json" \
  -d '[
    {"id": "eK_KWWxU6gY"},
    {"id": "BDD_Ppcnpfs"}
  ]'
```

**Request format:**

```json
[
  {"id": "eK_KWWxU6gY"},
  {"id": "BDD_Ppcnpfs"},
  {"id": "qkg29El9D5I"}
]
```

**Response format:**

```json
[
  {
    "success": true,
    "transcript": [
      {
        "text": "Today we're going to be looking at",
        "duration": "4.40",
        "offset": "0.24",
        "lang": "en"
      }
    ]
  },
  {
    "success": false,
    "error": "No transcript found for video ID 'invalid_id'"
  }
]
```

#### Get Available Languages

```http
GET /transcript/{video_id}/languages
```

Get information about available transcript languages for a video.

**Example:**

```bash
curl http://localhost:8000/transcript/dQw4w9WgXcQ/languages
```

#### Health Check

```http
GET /health
```

Check if the server is running.

#### Root Endpoint

```http
GET /
```

Get basic API information and links.

### Interactive Documentation

Visit `http://localhost:8000/docs` for interactive API documentation powered by FastAPI's automatic OpenAPI generation.

## API Reference

### Response Format

The main transcript endpoint returns an array of transcript segments:

```typescript
interface TranscriptSegment {
    text: string;      // The spoken text
    start: number;     // Start time in seconds
    duration: number;  // Duration in seconds
}
```

### Error Handling

The API returns appropriate HTTP status codes:

- `200`: Success
- `403`: Transcripts disabled for the video
- `404`: Video not found or no transcript available
- `429`: Too many requests (rate limited)
- `500`: Internal server error

### Video ID Format

Use the YouTube video ID (not the full URL):

- ✅ `dQw4w9WgXcQ`
- ❌ `https://www.youtube.com/watch?v=dQw4w9WgXcQ`

## Development

### Project Structure

```sh
transcript-server/
├── main.py              # FastAPI application
├── pyproject.toml       # Project configuration and dependencies
├── uv.lock             # Dependency lock file
├── README.md           # This file
└── .github/
    └── copilot-instructions.md  # GitHub Copilot instructions
```

### Adding Dependencies

```bash
uv add <package-name>
```

### Running in Development

```bash
uv run main.py
```

For auto-reload during development:

```bash
uv run uvicorn main:app --reload
```

## Dependencies

- **FastAPI**: Modern, fast web framework for building APIs
- **uvicorn**: ASGI server for running FastAPI
- **youtube-transcript-api**: Library for fetching YouTube transcripts

## License

This project is open source and available under the [MIT License](LICENSE).

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Troubleshooting

### Common Issues

1. **Video ID not found**: Make sure you're using the correct YouTube video ID
2. **No transcript available**: Some videos don't have transcripts or have them disabled
3. **Rate limiting**: YouTube may rate limit requests - try again later

### Getting Help

- Check the interactive docs at `/docs`
- Review error messages in the API responses
- Ensure the video ID is correct and the video exists
