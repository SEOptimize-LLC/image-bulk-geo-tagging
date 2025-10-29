import streamlit as st
import piexif
from PIL import Image
import io
import zipfile
from datetime import datetime
import tempfile
import os


def convert_to_degrees(value):
    """
    Convert decimal degrees to degrees, minutes, seconds format for EXIF.
    """
    abs_value = abs(value)
    degrees = int(abs_value)
    minutes = int((abs_value - degrees) * 60)
    seconds = int(((abs_value - degrees) * 60 - minutes) * 60 * 100)

    return ((degrees, 1), (minutes, 1), (seconds, 100))


def add_geotag_to_image(image_bytes, metadata):
    """
    Add geo-tagging and metadata to an image's EXIF data.

    Args:
        image_bytes: Image file bytes
        metadata: Dictionary containing title, description, keywords, address, latitude, longitude

    Returns:
        Modified image bytes
    """
    try:
        # Open image
        img = Image.open(io.BytesIO(image_bytes))

        # Load existing EXIF data or create new
        try:
            exif_dict = piexif.load(img.info.get("exif", b""))
        except:
            exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}

        # Ensure all required dictionaries exist
        if "0th" not in exif_dict:
            exif_dict["0th"] = {}
        if "Exif" not in exif_dict:
            exif_dict["Exif"] = {}
        if "GPS" not in exif_dict:
            exif_dict["GPS"] = {}

        # Add title (ImageDescription)
        if metadata.get("title"):
            exif_dict["0th"][piexif.ImageIFD.ImageDescription] = metadata["title"].encode("utf-8")

        # Add description (UserComment in Exif IFD)
        if metadata.get("description"):
            exif_dict["Exif"][piexif.ExifIFD.UserComment] = metadata["description"].encode("utf-8")

        # Add keywords (XPKeywords - Windows style keywords)
        if metadata.get("keywords"):
            # Convert keywords to UTF-16LE for Windows compatibility
            keywords_str = metadata["keywords"]
            exif_dict["0th"][piexif.ImageIFD.XPKeywords] = keywords_str.encode("utf-16le")

        # Add GPS coordinates if provided
        if metadata.get("latitude") is not None and metadata.get("longitude") is not None:
            lat = metadata["latitude"]
            lon = metadata["longitude"]

            # Convert to GPS format
            lat_deg = convert_to_degrees(lat)
            lon_deg = convert_to_degrees(lon)

            # Set GPS data
            exif_dict["GPS"][piexif.GPSIFD.GPSLatitudeRef] = "N" if lat >= 0 else "S"
            exif_dict["GPS"][piexif.GPSIFD.GPSLatitude] = lat_deg
            exif_dict["GPS"][piexif.GPSIFD.GPSLongitudeRef] = "E" if lon >= 0 else "W"
            exif_dict["GPS"][piexif.GPSIFD.GPSLongitude] = lon_deg

            # Add GPS version
            exif_dict["GPS"][piexif.GPSIFD.GPSVersionID] = (2, 3, 0, 0)

        # Add address as GPS processing method (custom field)
        if metadata.get("address"):
            # Store address in GPS Processing Method
            address_bytes = metadata["address"].encode("utf-8")
            exif_dict["GPS"][piexif.GPSIFD.GPSProcessingMethod] = b"ASCII\x00\x00\x00" + address_bytes

        # Convert EXIF dict to bytes
        exif_bytes = piexif.dump(exif_dict)

        # Save image with new EXIF data
        output = io.BytesIO()

        # Convert to RGB if necessary (for PNG or RGBA images)
        if img.mode in ("RGBA", "LA", "P"):
            rgb_img = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")
            rgb_img.paste(img, mask=img.split()[-1] if img.mode in ("RGBA", "LA") else None)
            img = rgb_img
        elif img.mode != "RGB":
            img = img.convert("RGB")

        # Save with EXIF data
        img.save(output, format="JPEG", exif=exif_bytes, quality=95)

        return output.getvalue()

    except Exception as e:
        st.error(f"Error processing image: {str(e)}")
        return None


def main():
    st.set_page_config(
        page_title="Bulk Image Geo-Tagging Tool",
        page_icon="📍",
        layout="wide"
    )

    st.title("📍 Bulk Image Geo-Tagging Tool")
    st.markdown("Add geo-tags and metadata to multiple images at once")

    # Sidebar for metadata input
    st.sidebar.header("Metadata Settings")
    st.sidebar.markdown("Enter the metadata to be added to all uploaded images:")

    # Input fields
    title = st.sidebar.text_input("Title", placeholder="e.g., Beautiful Sunset")
    description = st.sidebar.text_area("Description", placeholder="e.g., A stunning sunset over the mountains")
    keywords = st.sidebar.text_input("Keywords & Tags", placeholder="e.g., sunset, nature, landscape")
    address = st.sidebar.text_input("Address", placeholder="e.g., 123 Main St, City, Country")

    st.sidebar.markdown("---")
    st.sidebar.subheader("GPS Coordinates")

    col1, col2 = st.sidebar.columns(2)
    with col1:
        latitude = st.number_input("Latitude", min_value=-90.0, max_value=90.0, value=0.0, format="%.6f", step=0.000001)
    with col2:
        longitude = st.number_input("Longitude", min_value=-180.0, max_value=180.0, value=0.0, format="%.6f", step=0.000001)

    st.sidebar.markdown("*Example: San Francisco (37.7749, -122.4194)*")

    # Main content area
    st.header("Upload Images")
    uploaded_files = st.file_uploader(
        "Choose image files",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True,
        help="Upload one or more images to add geo-tags and metadata"
    )

    if uploaded_files:
        st.success(f"✓ {len(uploaded_files)} image(s) uploaded")

        # Show preview of metadata
        with st.expander("Preview Metadata", expanded=True):
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Text Metadata:**")
                if title:
                    st.write(f"• **Title:** {title}")
                if description:
                    st.write(f"• **Description:** {description}")
                if keywords:
                    st.write(f"• **Keywords:** {keywords}")
                if address:
                    st.write(f"• **Address:** {address}")

                if not any([title, description, keywords, address]):
                    st.info("No text metadata entered")

            with col2:
                st.markdown("**GPS Coordinates:**")
                if latitude != 0.0 or longitude != 0.0:
                    st.write(f"• **Latitude:** {latitude}°")
                    st.write(f"• **Longitude:** {longitude}°")
                    st.write(f"• **[View on map](https://www.google.com/maps?q={latitude},{longitude})**")
                else:
                    st.info("No GPS coordinates entered")

        # Process button
        if st.button("🏷️ Process Images", type="primary", use_container_width=True):
            if not any([title, description, keywords, address, latitude != 0.0, longitude != 0.0]):
                st.warning("⚠️ Please enter at least one metadata field before processing")
            else:
                # Prepare metadata dictionary
                metadata = {
                    "title": title,
                    "description": description,
                    "keywords": keywords,
                    "address": address,
                    "latitude": latitude if (latitude != 0.0 or longitude != 0.0) else None,
                    "longitude": longitude if (latitude != 0.0 or longitude != 0.0) else None
                }

                # Process images
                progress_bar = st.progress(0)
                status_text = st.empty()

                processed_images = []

                for idx, uploaded_file in enumerate(uploaded_files):
                    status_text.text(f"Processing {uploaded_file.name}...")

                    # Read image bytes
                    image_bytes = uploaded_file.read()

                    # Process image
                    processed_bytes = add_geotag_to_image(image_bytes, metadata)

                    if processed_bytes:
                        processed_images.append({
                            "name": uploaded_file.name,
                            "bytes": processed_bytes
                        })

                    # Update progress
                    progress_bar.progress((idx + 1) / len(uploaded_files))

                status_text.text("Processing complete!")

                if processed_images:
                    st.success(f"✓ Successfully processed {len(processed_images)} image(s)")

                    # Create download section
                    st.header("Download Processed Images")

                    if len(processed_images) == 1:
                        # Single file download
                        st.download_button(
                            label="⬇️ Download Image",
                            data=processed_images[0]["bytes"],
                            file_name=f"geotagged_{processed_images[0]['name']}",
                            mime="image/jpeg",
                            use_container_width=True
                        )
                    else:
                        # Multiple files - create ZIP
                        zip_buffer = io.BytesIO()
                        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                            for img in processed_images:
                                zip_file.writestr(f"geotagged_{img['name']}", img["bytes"])

                        zip_buffer.seek(0)

                        st.download_button(
                            label=f"⬇️ Download All Images (ZIP)",
                            data=zip_buffer.getvalue(),
                            file_name=f"geotagged_images_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                            mime="application/zip",
                            use_container_width=True
                        )
                else:
                    st.error("❌ Failed to process images. Please try again.")

    else:
        st.info("👆 Upload images using the file uploader above to get started")

    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666;'>
            <small>Built with Streamlit • Supports JPG, JPEG, and PNG formats</small>
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
