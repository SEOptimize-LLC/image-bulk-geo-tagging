# Image Bulk Geo-Tagging Tool

A powerful and user-friendly Streamlit application that allows you to add geo-tags and metadata to multiple images at once. Perfect for photographers, content creators, and anyone who needs to organize and tag their image collections efficiently.

## Features

- **True Bulk Processing**: Upload and process hundreds or thousands of images
- **Complete Metadata Support**:
  - Title
  - Description
  - Keywords & Tags
  - Physical Address
  - GPS Coordinates (Latitude & Longitude)
- **EXIF Data Integration**: All metadata is embedded directly into the image EXIF data
- **Memory-Optimized**: Uses temporary files and garbage collection for efficient processing
- **User-Friendly Interface**: Clean, intuitive Streamlit interface
- **Flexible Download Options**:
  - Single image download for one file
  - ZIP archive for multiple images
- **Format Support**: Works with JPG, JPEG, and PNG image formats
- **Cloud Ready**: Optimized for deployment on Streamlit Cloud
- **Large Upload Support**: Up to 2GB total upload size

## Live Demo

[Deploy this app to Streamlit Cloud](#deployment) to see it in action!

## Installation

### Local Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/image-bulk-geo-tagging.git
cd image-bulk-geo-tagging
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
streamlit run app.py
```

5. Open your browser and navigate to `http://localhost:8501`

## Usage

1. **Enter Metadata** (in the sidebar):
   - **Title**: Add a title for your images
   - **Description**: Provide a detailed description
   - **Keywords & Tags**: Enter relevant keywords (comma-separated)
   - **Address**: Specify the physical location
   - **GPS Coordinates**: Enter latitude and longitude values
     - Latitude: -90 to 90 (negative for South)
     - Longitude: -180 to 180 (negative for West)

2. **Upload Images**:
   - Click the file uploader
   - Select one or more images (JPG, JPEG, or PNG)
   - Multiple files can be uploaded at once

3. **Preview Metadata**:
   - Review the metadata you've entered
   - Check the GPS coordinates on a map (if provided)

4. **Process Images**:
   - Click the "Process Images" button
   - Wait for processing to complete
   - Watch the progress bar

5. **Download Results**:
   - Single image: Direct download button
   - Multiple images: Download as ZIP file
   - Processed images are saved in JPEG format with embedded EXIF data

## Deployment

### Streamlit Cloud

1. Fork this repository to your GitHub account

2. Go to [share.streamlit.io](https://share.streamlit.io)

3. Sign in with your GitHub account

4. Click "New app"

5. Configure your app:
   - Repository: Select your forked repository
   - Branch: `main` (or your default branch)
   - Main file path: `app.py`

6. Click "Deploy"

Your app will be live in a few minutes!

## Bulk Processing Capabilities

### Upload Limits

- **Maximum upload size**: 2000 MB (2 GB) total
- **File limit**: No hard limit on number of files
- **Recommended batch size**: 100-500 images per session for optimal performance
- **Individual file size**: No specific limit (constrained by total upload size)

### Performance Optimization

The application is specifically optimized for bulk operations:

1. **Memory-Efficient Processing**:
   - Processes images one at a time
   - Immediately writes processed images to temporary files
   - Clears memory after each image using garbage collection
   - Prevents memory overflow even with thousands of images

2. **Streaming ZIP Creation**:
   - Reads processed images from disk (not memory)
   - Creates ZIP archives efficiently
   - Displays final file size

3. **Error Handling**:
   - Continues processing if individual images fail
   - Reports success/failure count
   - Shows detailed error messages for failed images

### Real-World Capacity

Based on typical image sizes:

| Image Size | Approximate Images per 2GB |
|------------|---------------------------|
| 1 MB (compressed) | ~2000 images |
| 5 MB (high-quality) | ~400 images |
| 10 MB (RAW/large) | ~200 images |

**Note**: While you can upload up to 2GB at once, processing 100-500 images per batch is recommended for the best user experience on Streamlit Cloud.

## Technical Details

### EXIF Data Mapping

The application maps your input to the following EXIF fields:

- **Title** → `ImageDescription` (0th IFD)
- **Description** → `UserComment` (Exif IFD)
- **Keywords** → `XPKeywords` (0th IFD, UTF-16LE encoded)
- **GPS Coordinates** → GPS IFD fields:
  - `GPSLatitude` and `GPSLatitudeRef`
  - `GPSLongitude` and `GPSLongitudeRef`
  - `GPSVersionID`
- **Address** → `GPSProcessingMethod` (GPS IFD)

### Image Processing

- PNG and RGBA images are converted to RGB/JPEG format
- EXIF data is preserved and enhanced
- Output quality is set to 95% to maintain image quality
- Original images are not modified (new files are created)

## Dependencies

- **Streamlit** (1.29.0): Web application framework
- **Pillow** (10.1.0): Image processing library
- **piexif** (1.1.3): EXIF data manipulation

## Examples

### Example 1: Tourist Photos
```
Title: Eiffel Tower Visit
Description: Beautiful view of the Eiffel Tower during sunset
Keywords: Eiffel Tower, Paris, France, sunset, travel
Address: Champ de Mars, 5 Avenue Anatole France, 75007 Paris, France
Latitude: 48.858370
Longitude: 2.294481
```

### Example 2: Real Estate Photography
```
Title: Modern Downtown Apartment
Description: Spacious 2-bedroom apartment with city views
Keywords: real estate, apartment, downtown, modern, luxury
Address: 123 Main Street, San Francisco, CA 94102
Latitude: 37.779530
Longitude: -122.419420
```

### Example 3: Nature Photography
```
Title: Mountain Lake Reflection
Description: Pristine alpine lake reflecting mountain peaks at dawn
Keywords: nature, landscape, mountains, lake, reflection, alpine
Address: Moraine Lake, Banff National Park, Alberta, Canada
Latitude: 51.332760
Longitude: -116.185470
```

## Tips for Best Results

1. **GPS Coordinates**: Use Google Maps to find accurate coordinates:
   - Right-click on a location
   - Select the coordinates to copy them

2. **Keywords**: Use comma-separated values for better organization:
   - `landscape, nature, mountains, sunset`

3. **Image Format**:
   - JPG/JPEG files maintain their format
   - PNG files are converted to JPEG (EXIF support requirement)

4. **Batch Processing**:
   - Process similar images together with the same metadata
   - For very large batches (1000+), consider splitting into multiple sessions
   - 100-500 images per batch is optimal

5. **Upload Size**:
   - The app supports up to 2GB total upload size
   - Monitor the displayed upload size after selecting files
   - App shows progress during processing

6. **Memory Management**:
   - Processing is optimized to handle large batches
   - Each image is processed individually and saved to disk
   - Failed images won't stop the entire batch

## Troubleshooting

### Images fail to process
- Ensure images are valid JPG, JPEG, or PNG files
- Check that files are not corrupted
- Verify image file sizes are reasonable

### GPS coordinates not showing
- Make sure coordinates are within valid ranges:
  - Latitude: -90 to 90
  - Longitude: -180 to 180
- Use decimal degrees format (e.g., 37.7749, not 37°46'30"N)

### ZIP download not working
- Try processing fewer images at once
- Check your browser's download settings
- Ensure you have sufficient disk space

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open source and available under the MIT License.

## Support

If you encounter any issues or have questions, please open an issue on GitHub.

## Acknowledgments

Built with:
- [Streamlit](https://streamlit.io/) - The web framework
- [Pillow](https://python-pillow.org/) - Image processing
- [piexif](https://piexif.readthedocs.io/) - EXIF manipulation

---

Made with ❤️ for photographers and content creators
