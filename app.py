import streamlit as st
import piexif
from PIL import Image
import io
import zipfile
from datetime import datetime
import tempfile
import os
import gc


def convert_to_degrees(value):
    """
    Convert decimal degrees to degrees, minutes, seconds format for EXIF.
    """
    abs_value = abs(value)
    degrees = int(abs_value)
    minutes = int((abs_value - degrees) * 60)
    seconds = int(((abs_value - degrees) * 60 - minutes) * 60 * 100)

    return ((degrees, 1), (minutes, 1), (seconds, 100))


def add_geotag_to_image(image_bytes, metadata, original_format="JPEG", jpeg_quality=95):
    """
    Add geo-tagging and metadata to an image's EXIF data.

    Args:
        image_bytes: Image file bytes
        metadata: Dictionary containing title, description, keywords, address, latitude, longitude
        original_format: Original image format (JPEG, PNG, etc.)
        jpeg_quality: JPEG quality (1-100) when converting to JPEG

    Returns:
        Tuple of (modified image bytes, error message) or (None, error message) on failure
    """
    try:
        # Open image
        img = Image.open(io.BytesIO(image_bytes))
        original_mode = img.mode

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

        # Save with EXIF data (always JPEG for EXIF support)
        img.save(output, format="JPEG", exif=exif_bytes, quality=jpeg_quality)

        return output.getvalue(), None

    except Exception as e:
        return None, str(e)


def main():
    st.set_page_config(
        page_title="Bulk Image Geo-Tagging Tool",
        page_icon="📍",
        layout="wide"
    )

    st.title("📍 Bulk Image Geo-Tagging Tool")
    st.markdown("Add geo-tags and metadata to images from a ZIP archive")

    # Show capabilities
    with st.expander("ℹ️ Upload Limits & Recommendations", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            **Upload Limits:**
            - Max total upload: 2000 MB (2 GB)
            - Supported formats: ZIP files containing JPG, JPEG, PNG images
            - Folder structure will be preserved in output
            """)
        with col2:
            st.markdown("""
            **Recommendations:**
            - ZIP should contain images in YEAR > MONTH folder structure
            - Example: 2024/01/image1.jpg, 2024/02/image2.jpg
            - Process 100-500 images per batch for optimal performance
            - Memory-optimized for bulk operations
            """)

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

    st.sidebar.markdown("---")
    st.sidebar.subheader("Output Settings")
    jpeg_quality = st.sidebar.slider(
        "JPEG Quality",
        min_value=1,
        max_value=100,
        value=95,
        help="Higher quality = larger file size. Images are converted to JPEG to support EXIF metadata."
    )
    st.sidebar.info("Note: All images are converted to JPEG format to ensure EXIF metadata compatibility.")

    # Main content area
    st.header("Upload ZIP Archive")
    uploaded_zip = st.file_uploader(
        "Choose a ZIP file containing images",
        type=["zip"],
        accept_multiple_files=False,
        help="Upload a ZIP file with images organized in YEAR > MONTH folder structure"
    )

    if uploaded_zip:
        # Calculate total size
        zip_size_mb = uploaded_zip.size / (1024 * 1024)

        st.success(f"✓ ZIP file uploaded ({zip_size_mb:.2f} MB)")

        # Extract and analyze ZIP structure
        try:
            with zipfile.ZipFile(io.BytesIO(uploaded_zip.read()), 'r') as zip_ref:
                file_list = [f for f in zip_ref.namelist() if not f.endswith('/') and f.lower().endswith(('.jpg', '.jpeg', '.png'))]
                total_images = len(file_list)

                # Analyze folder structure
                folders = set()
                for file_path in file_list:
                    folder = os.path.dirname(file_path)
                    if folder:
                        folders.add(folder)

                st.info(f"📁 Found {total_images} image(s) in {len(folders)} folder(s)")

                # Show folder structure preview
                if folders:
                    with st.expander("Preview Folder Structure", expanded=False):
                        sorted_folders = sorted(folders)
                        preview_text = "\n".join([f"📁 {folder}" for folder in sorted_folders[:20]])
                        if len(folders) > 20:
                            preview_text += f"\n... and {len(folders) - 20} more folders"
                        st.text(preview_text)

            # Reset file pointer for later processing
            uploaded_zip.seek(0)

        except Exception as e:
            st.error(f"❌ Error reading ZIP file: {str(e)}")
            st.stop()

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

                # Process images with memory-efficient approach
                progress_bar = st.progress(0)
                status_text = st.empty()

                # Create temporary directory for processed images
                temp_dir = tempfile.mkdtemp()
                processed_files = []
                failed_files = []
                success_count = 0

                try:
                    # Extract and process ZIP file
                    uploaded_zip.seek(0)
                    with zipfile.ZipFile(io.BytesIO(uploaded_zip.read()), 'r') as zip_ref:
                        # Get all image files from ZIP
                        image_files = [f for f in zip_ref.namelist() if not f.endswith('/') and f.lower().endswith(('.jpg', '.jpeg', '.png'))]

                        for idx, file_path in enumerate(image_files):
                            status_text.text(f"Processing {idx + 1}/{len(image_files)}: {file_path}...")

                            image_bytes = None
                            try:
                                # Read image bytes from ZIP
                                image_bytes = zip_ref.read(file_path)

                                # Get original format
                                original_format = file_path.split('.')[-1].upper()

                                # Process image
                                processed_bytes, error = add_geotag_to_image(
                                    image_bytes,
                                    metadata,
                                    original_format=original_format,
                                    jpeg_quality=jpeg_quality
                                )

                                if processed_bytes and error is None:
                                    # Preserve folder structure in output
                                    # Create directory structure in temp folder
                                    output_file_path = os.path.join(temp_dir, file_path)
                                    output_dir = os.path.dirname(output_file_path)

                                    if output_dir:
                                        os.makedirs(output_dir, exist_ok=True)

                                    # Save to temporary file with original folder structure
                                    with open(output_file_path, "wb") as f:
                                        f.write(processed_bytes)

                                    processed_files.append({
                                        "name": os.path.basename(file_path),
                                        "path": output_file_path,
                                        "relative_path": file_path
                                    })
                                    success_count += 1
                                else:
                                    # Track failed images and save original file
                                    failed_file_path = os.path.join(temp_dir, "failed", file_path)
                                    failed_dir = os.path.dirname(failed_file_path)
                                    if failed_dir:
                                        os.makedirs(failed_dir, exist_ok=True)

                                    with open(failed_file_path, "wb") as f:
                                        f.write(image_bytes)

                                    failed_files.append({
                                        "name": file_path,
                                        "error": error or "Unknown error",
                                        "path": failed_file_path
                                    })

                                # Clear memory
                                if processed_bytes:
                                    del processed_bytes
                                if image_bytes:
                                    del image_bytes
                                gc.collect()

                            except Exception as e:
                                # Save original file even if exception occurred
                                if image_bytes:
                                    failed_file_path = os.path.join(temp_dir, "failed", file_path)
                                    failed_dir = os.path.dirname(failed_file_path)
                                    if failed_dir:
                                        os.makedirs(failed_dir, exist_ok=True)

                                    with open(failed_file_path, "wb") as f:
                                        f.write(image_bytes)

                                    failed_files.append({
                                        "name": file_path,
                                        "error": str(e),
                                        "path": failed_file_path
                                    })
                                else:
                                    failed_files.append({
                                        "name": file_path,
                                        "error": str(e),
                                        "path": None
                                    })

                            # Update progress
                            progress_bar.progress((idx + 1) / len(image_files))

                    status_text.text("Processing complete!")

                    # Show summary with clear breakdown
                    st.markdown("### Processing Summary")
                    total_processed = success_count + len(failed_files)
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Images", total_processed)
                    with col2:
                        st.metric("Successfully Processed", success_count, delta=None if success_count == total_processed else f"{success_count - total_processed}")
                    with col3:
                        st.metric("Failed", len(failed_files), delta=None if len(failed_files) == 0 else f"-{len(failed_files)}")

                    # Show failed files if any
                    if failed_files:
                        st.warning(f"⚠️ {len(failed_files)} image(s) failed to process")
                        with st.expander("View Failed Images Details", expanded=False):
                            # Use text area for better performance with many failures
                            failed_text = "\n".join([f"{i+1}. {f['name']}: {f['error']}" for i, f in enumerate(failed_files)])
                            st.text_area(
                                "Failed images and error details:",
                                value=failed_text,
                                height=300,
                                disabled=True
                            )

                    if processed_files:
                        st.success(f"✓ Successfully processed {success_count} out of {total_processed} image(s)")

                        # Create download section
                        st.header("Download Processed Images")

                        # Create ZIP from temp files with preserved folder structure
                        zip_buffer = io.BytesIO()
                        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                            for img_info in processed_files:
                                # Add file to ZIP with original folder structure (relative_path)
                                zip_file.write(img_info["path"], img_info['relative_path'])

                        zip_buffer.seek(0)

                        st.download_button(
                            label=f"⬇️ Download Geotagged Images (ZIP)",
                            data=zip_buffer.getvalue(),
                            file_name=f"geotagged_images_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                            mime="application/zip",
                            use_container_width=True
                        )

                        # Show size info
                        zip_size_mb = len(zip_buffer.getvalue()) / (1024 * 1024)
                        st.info(f"📦 ZIP file size: {zip_size_mb:.2f} MB | Folder structure preserved")

                        # Add failed images download section (if any)
                        if failed_files:
                            st.markdown("---")
                            st.subheader("❌ Failed Images")
                            st.warning(f"{len(failed_files)} image(s) could not be processed")

                            try:
                                # Create ZIP of failed images IN MEMORY before cleanup
                                failed_zip_buffer = io.BytesIO()
                                files_with_data = []

                                # Load all failed image data into memory BEFORE creating ZIP
                                for failed in failed_files:
                                    if failed.get('path') and os.path.exists(failed['path']):
                                        with open(failed['path'], 'rb') as f:
                                            files_with_data.append({
                                                'name': failed['name'],
                                                'data': f.read(),
                                                'error': failed['error']
                                            })

                                # Create ZIP from in-memory data
                                with zipfile.ZipFile(failed_zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                                    for file_data in files_with_data:
                                        zip_file.writestr(file_data['name'], file_data['data'])

                                    # Add error log
                                    error_log = "\n".join([f"{f['name']}: {f['error']}" for f in files_with_data])
                                    zip_file.writestr("_ERROR_LOG.txt", error_log)

                                # Get ZIP data into variable BEFORE cleanup
                                failed_zip_data = failed_zip_buffer.getvalue()
                                failed_zip_size_mb = len(failed_zip_data) / (1024 * 1024)

                                col1, col2 = st.columns([2, 1])
                                with col1:
                                    st.download_button(
                                        label=f"⬇️ Download Failed Images (ZIP)",
                                        data=failed_zip_data,
                                        file_name=f"failed_images_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                                        mime="application/zip",
                                        use_container_width=True,
                                        help="Download the original files that failed processing, plus error log"
                                    )
                                with col2:
                                    st.metric("ZIP Size", f"{failed_zip_size_mb:.2f} MB")

                                st.info("💡 These are the original uploaded files that couldn't be processed. Use a different tool to add geo-tags to these images.")

                            except Exception as e:
                                st.error(f"❌ Error creating failed images ZIP: {str(e)}")
                                st.info("Failed images list is still available below.")

                        # Add file lists download section
                        st.markdown("---")
                        st.subheader("📋 File Lists for Tracking")
                        col1, col2 = st.columns(2)

                        with col1:
                            # Successfully processed files list with folder structure
                            success_list = "\n".join([f['relative_path'] for f in processed_files])
                            st.download_button(
                                label="⬇️ Download Success List (TXT)",
                                data=success_list,
                                file_name=f"successfully_processed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                                mime="text/plain",
                                help="List of file paths that were successfully processed"
                            )
                            st.caption(f"✓ {len(processed_files)} files")

                        with col2:
                            # Failed files list (if any)
                            if failed_files:
                                failed_list = "\n".join([f"{f['name']}: {f['error']}" for f in failed_files])
                                st.download_button(
                                    label="⬇️ Download Failed List (TXT)",
                                    data=failed_list,
                                    file_name=f"failed_list_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                                    mime="text/plain",
                                    help="List of file paths that failed processing with error details"
                                )
                                st.caption(f"❌ {len(failed_files)} files")
                            else:
                                st.caption("✓ No failed files")

                    else:
                        st.error("❌ Failed to process images. Please try again.")

                finally:
                    # Cleanup temporary files
                    import shutil
                    try:
                        shutil.rmtree(temp_dir)
                    except:
                        pass

    else:
        st.info("👆 Upload a ZIP file containing images organized in YEAR > MONTH folder structure to get started")

    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666;'>
            <small>Built with Streamlit • Supports ZIP files containing JPG, JPEG, and PNG images • Preserves folder structure</small>
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
