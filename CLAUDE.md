# Virginia Tech Course Extractor Guidelines

## Commands

### Backend
- Run server: `cd backend && python -m app.main`
- Run tests: `cd backend && python -m backend.tests.pdf_processor_test`
- Run S3 tests: `cd backend && python -m backend.tests.test_s3`

### Frontend
- Development: `cd frontend && npm run dev`
- Build: `cd frontend && npm run build`
- Preview build: `cd frontend && npm run preview`

## Code Style Guidelines

### Python
- Use type hints for all function parameters and return values
- Format imports: standard library → third-party → local modules
- Use snake_case for variables/functions and PascalCase for classes
- Error handling: use try/except blocks with specific exceptions
- Log errors with appropriate severity levels

### JavaScript/React
- Use ESM import/export syntax
- Prefer functional components with hooks
- Maintain consistent component structure
- Use async/await for asynchronous operations
- Handle API errors with appropriate user feedback

## Logging
- Backend logs go to `logs/backend/`
- Frontend logs go to `logs/frontend/`