# Character Gallery Feature

## Overview

The character gallery feature has been added to the character detail page to allow players and staff to upload and manage multiple images for each character.

## Features

### 1. Gallery Button
- Located below the main character image
- Shows count of images in gallery
- Toggles between main character info and gallery view

### 2. Gallery View
- Grid display of character images
- Thumbnail previews with captions
- Click to view full-size images in modal
- Upload button for authorized users
- Delete buttons for each image (authorized users only)

### 3. Image Upload
- File upload form with caption field
- Supports JPG, PNG, GIF, WebP formats
- Maximum file size: 5MB
- Automatic unique filename generation
- Images stored in character-specific directories

### 4. Permissions
- Staff members can upload/delete any character's images
- Character owners can upload/delete their own character's images
- All users can view galleries

## Technical Implementation

### Backend (views.py)
- `get_character_images()` - Retrieves character's image gallery
- `save_character_image()` - Handles file upload and storage
- `remove_character_image()` - Deletes images from gallery
- `upload_character_image()` - API endpoint for uploads
- `delete_character_image()` - API endpoint for deletions

### Frontend (character_detail.html)
- Gallery toggle functionality
- Modal dialogs for image upload and viewing
- AJAX calls for upload/delete operations
- Responsive grid layout for image thumbnails

### Data Storage
- Images stored using Django's file storage system
- Gallery metadata stored in character attributes
- Each image has: ID, filename, path, caption, URL, upload timestamp

### URL Routes
- `/roster/detail/<char_name>/<char_id>/upload-image/` - Image upload
- `/roster/detail/<char_name>/<char_id>/delete-image/` - Image deletion

## Usage

1. Navigate to a character detail page
2. Click the "📸 Gallery" button to view/manage images
3. Use "➕ Add Image" to upload new images (if authorized)
4. Click thumbnail images to view full size
5. Use "🗑️ Delete" buttons to remove images (if authorized)
6. Click "✖️ Close Gallery" to return to character info

## File Structure

```
web/
├── roster/
│   ├── views.py (gallery functions)
│   ├── urls.py (gallery routes)
│   └── templates/roster/
│       └── character_detail.html (gallery UI)
└── static/
    └── character_images/ (image storage)
``` 