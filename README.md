# VT COE Graduate Course Enrollment Reporting Tool

A containerized solution for extracting course data from PDF timetables

## Overview

This application provides a user-friendly interface for processing Virginia Tech timetable PDFs and extracting structured course data. It uses metadata fields (program, semester, year) for better organization and outputs both individual and combined CSV files.

## System Requirements

- Windows 10/11, macOS, or Linux
- Docker Desktop installed and running
- Minimum 4GB RAM available
- Minimum 10GB free disk space
- Internet connection (for initial setup only)

## Quick Start

1. Install Docker Desktop from [docker.com](https://www.docker.com/products/docker-desktop)
2. Extract this package to your desired location
3. Double-click `start_extractor.bat` (Windows) or run `./start_extractor.sh` (Mac/Linux)
4. Wait for your browser to open automatically to the application
5. To stop, use `stop_extractor.bat` or `stop_extractor.sh`

## Step-by-Step User Guide

Please see: [VT COE Graduate Course Enrollment Reporting Tool: Step-by-Step Guide](https://virginiatech.sharepoint.com/:w:/r/sites/COEGraduateandProfessionalStudies/Shared%20Documents/GPS/GPS%20Enrollments/VT%20Course%20Extractor%20Step-by-Step%20Guide.docx?d=w7147911a1af14dc69033e6024aa6a378&csf=1&web=1&e=Ygnxwf)

## Folder Structure

```
course-extractor/
├── data/               # Output folder for CSV files
├── logs/               # Application logs
├── frontend/          # Web interface files
├── backend/           # Processing logic
└── setup/             # Setup and configuration files
```

See `./file-structure.txt` for a detailed breakdown of the folder structure.

## Usage Instructions

1. **Starting the Application**
   - Run the start script
   - Wait for the "Application is running!" message
   - The web interface will open automatically

2. **Processing PDFs**
   - Drag and drop PDF files onto the interface or click "Choose Files" to select them
   - Fill in metadata fields (program, semester, year) for each file
   - Click "Extract Course Data"
   - Wait for processing to complete

3. **Accessing Results**
   - Individual CSVs will be saved in `data/individual/`
   - Combined CSV will be saved in `data/combined/`
   - Underenrolled courses (fewer than 6 students) will be saved in a separate CSV
   - Download links will appear after processing

4. **Monitoring & Troubleshooting**
   - Check `logs/` folder for detailed logs
   - The interface will show processing status and errors
   - System monitor shows resource usage

## Error Recovery

Common issues and solutions:

1. **PDF Processing Errors**
   - Verify PDF is not corrupted
   - Check if PDF is password protected
   - Ensure PDF contains text (not just images)

2. **System Issues**
   - Check Docker Desktop is running
   - Verify system has enough memory
   - Ensure enough disk space is available

3. **Network Issues**
   - Verify Docker network is functioning
   - Check if containers are running
   - Restart Docker Desktop if needed

## Maintenance

- Logs are automatically rotated daily
- Old logs are compressed after 7 days
- Temporary files are cleaned up on shutdown
- System monitoring runs continuously

## Support

For technical support:
1. Check the logs in the `logs/` directory
2. Review the error messages in the web interface
3. Contact technical support with the log files if needed

## Security Notes

- All processing is done locally
- No data is sent to external services
- PDFs and extracted data remain on your system
- Models are downloaded once and cached locally

## Updating

1. Stop the application using the stop script
2. Replace the application folder with the new version
3. Start the application using the start script
4. The system will automatically update as needed

## Advanced Configuration

Power users can modify:
- `.env` file for environment variables
- `docker-compose.yml` for container settings
- `config/` directory for application settings