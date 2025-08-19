# QR Code Generator Pro - Documentation

## Overview

QR Code Generator Pro is a modern, professional desktop application built with Python and PySide6 that allows users to generate, customize, and manage QR codes with advanced features. The application follows the MVC (Model-View-Controller) architecture pattern and provides a comprehensive solution for both individual and bulk QR code generation.

## Features

### Core QR Generation
- **Multiple QR Types**: Text, URLs, phone numbers, email, WiFi credentials, SMS messages, and vCard
- **Live Preview**: Real-time QR code preview with instant updates
- **Customization Options**: 
  - Foreground and background colors
  - Size and border customization
  - Error correction levels (L, M, Q, H)
  - DPI settings for high-resolution output
  - Logo overlay support
- **Export Formats**: PNG and SVG with high-resolution support

### Excel Integration (Bulk Generation)
- **Excel File Import**: Support for .xlsx and .xls files
- **Column Selection**: Choose which columns to include in QR content
- **Template System**: Customizable content templates with placeholders
- **Batch Processing**: Generate multiple QR codes simultaneously
- **Progress Tracking**: Real-time progress updates during generation
- **Automatic Naming**: Generate filenames based on selected columns

### QR Code Reading
- **Image Import**: Load QR codes from various image formats
- **Drag & Drop**: Support for drag-and-drop image input
- **Multiple QR Detection**: Read multiple QR codes from a single image
- **Content Display**: Show decoded content with metadata
- **Copy to Clipboard**: Easy content copying functionality

### Advanced Features
- **Theme Support**: Light and Dark themes with system integration
- **Settings Persistence**: Save and restore user preferences
- **Recent Files**: Track and access recently used files
- **Multi-language Support**: Framework for internationalization
- **Responsive UI**: Modern, intuitive interface design

## Installation

### Prerequisites
- Python 3.8 or higher
- Windows 10 or later (for executable)
- Internet connection (for dependency installation)

### Quick Setup
1. Clone or download the project
2. Run the setup script:
   ```bash
   python setup.py
   ```
3. Start the application:
   ```bash
   python main.py
   ```

### Manual Installation
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Create sample data (optional):
   ```bash
   python sample_data.py
   ```
3. Run the application:
   ```bash
   python main.py
   ```

## Usage Guide

### Individual QR Code Generation

1. **Select QR Type**: Choose from Text, URL, Phone, Email, WiFi, SMS, or vCard
2. **Enter Content**: 
   - For simple types: Enter the content directly
   - For complex types (WiFi, SMS, vCard): Use comma-separated values
3. **Customize Appearance**:
   - Choose foreground and background colors
   - Adjust size and border settings
   - Select error correction level
   - Set DPI for output quality
4. **Add Logo** (optional): Select an image to overlay on the QR code
5. **Preview**: See real-time preview of the QR code
6. **Save**: Export in PNG or SVG format

### Bulk QR Generation from Excel

1. **Load Excel File**: Use "Load Excel File" button or drag-and-drop
2. **Select Columns**: Choose which columns to include in QR content
3. **Create Template**: Define content template using placeholders (e.g., `{Name} - {Email}`)
4. **Configure Output**:
   - Select filename column for automatic naming
   - Choose output directory
5. **Validate**: Check configuration before generation
6. **Generate**: Start batch processing with progress tracking

### QR Code Reading

1. **Load Image**: Use "Load Image" button or drag-and-drop
2. **Auto-read**: QR codes are automatically detected and decoded
3. **View Results**: See decoded content and metadata
4. **Copy Content**: Use "Copy to Clipboard" for easy access

### Settings Configuration

1. **General Settings**: Language, default directories, recent files
2. **QR Settings**: Default colors, size, border, error correction, DPI
3. **Appearance**: Theme selection, window preferences
4. **Advanced**: Performance settings, export preferences

## File Formats

### Supported Input Formats
- **Excel**: .xlsx, .xls
- **Images**: .png, .jpg, .jpeg, .bmp, .gif, .tiff, .webp

### Supported Output Formats
- **PNG**: High-quality raster format with customizable DPI
- **SVG**: Scalable vector format for unlimited scaling

## QR Code Types and Formats

### Text
- **Format**: Plain text
- **Example**: "Hello World"

### URL
- **Format**: Website URL
- **Example**: "https://example.com"
- **Auto-formatting**: Adds https:// if not present

### Phone Number
- **Format**: Phone number with optional country code
- **Example**: "+1-555-123-4567"
- **Output**: tel:+15551234567

### Email
- **Format**: Email address with optional subject and body
- **Example**: "user@example.com,Subject,Message body"
- **Output**: mailto:user@example.com?subject=Subject&body=Message body

### WiFi
- **Format**: SSID,Password,Security
- **Example**: "MyWiFi,password123,WPA"
- **Output**: WIFI:S:MyWiFi;T:WPA;P:password123;;

### SMS
- **Format**: Phone,Message
- **Example**: "+1-555-123-4567,Hello from QR code"
- **Output**: sms:+15551234567?body=Hello from QR code

### vCard
- **Format**: Name,Phone,Email,Company,Title
- **Example**: "John Doe,+1-555-123-4567,john@example.com,Company,Manager"
- **Output**: vCard format with contact information

## Excel Template Examples

### Contact Information
```
Name,Email,Phone,Company,Position
John Smith,john@example.com,+1-555-0101,Tech Corp,Engineer
```

**QR Template**: `{Name} - {Email}`
**Filename Column**: Name

### Product Information
```
Product,Price,SKU,Description
Widget A,29.99,WA001,High-quality widget
```

**QR Template**: `Product: {Product} | Price: ${Price} | SKU: {SKU}`
**Filename Column**: SKU

## Architecture

### MVC Pattern
- **Models**: Data structures and business logic
  - `QRData`: QR code content and metadata
  - `QRCodeSettings`: Generation parameters
  - `ExcelDataManager`: Excel file operations
- **Views**: User interface components
  - `MainWindow`: Primary application window
  - `QRGeneratorTab`: Individual QR generation
  - `BulkGeneratorTab`: Excel-based bulk generation
  - `QRReaderTab`: QR code reading interface
  - `SettingsTab`: Application settings
- **Controllers**: Business logic coordination
  - `QRController`: Main application controller

### Key Components
- **QRCodeGenerator**: Core QR generation engine
- **QRCodeReader**: QR code decoding functionality
- **SettingsManager**: Application settings persistence
- **ThemeManager**: UI theming system

## Building Executable

### Prerequisites
- PyInstaller (automatically installed by build script)

### Build Process
```bash
python build_exe.py
```

### Output
- **Executable**: `dist/QR_Code_Generator_Pro.exe`
- **Installer Package**: `installer/` directory

## Configuration Files

### Settings Storage
- **Location**: `config/settings.json`
- **Format**: JSON with user preferences
- **Auto-backup**: Settings are automatically saved

### Recent Files
- **Storage**: Part of settings file
- **Limit**: Configurable (default: 10 files)
- **Access**: Via File menu or toolbar

## Troubleshooting

### Common Issues

#### Dependencies Not Found
**Error**: "Missing required dependencies"
**Solution**: Run `python setup.py` to install dependencies

#### Excel File Loading Issues
**Error**: "Failed to load Excel file"
**Solution**: 
- Ensure file is not corrupted
- Check file format (.xlsx or .xls)
- Verify file is not open in another application

#### QR Code Generation Errors
**Error**: "Failed to generate QR code"
**Solution**:
- Check content length (QR codes have size limits)
- Verify content format for complex types
- Try different error correction level

#### Image Reading Issues
**Error**: "No QR codes found"
**Solution**:
- Ensure image contains a valid QR code
- Check image quality and resolution
- Verify QR code is not damaged or obscured

### Performance Optimization

#### Large Excel Files
- Use appropriate error correction levels
- Consider processing in smaller batches
- Monitor system memory usage

#### High-Resolution Output
- Adjust DPI settings based on needs
- Use SVG format for unlimited scaling
- Consider logo size for readability

## Development

### Project Structure
```
qr-generator-pro/
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
├── setup.py               # Setup script
├── build_exe.py           # Build script
├── sample_data.py         # Sample data generator
├── src/                   # Source code
│   ├── models/           # Data models
│   ├── views/            # UI components
│   ├── controllers/      # Business logic
│   └── utils/            # Utility functions
├── assets/               # Images and resources
├── locales/              # Translation files
└── config/               # Configuration files
```

### Adding New Features

#### New QR Code Type
1. Add type to `QRType` enum in `models/qr_data.py`
2. Implement formatting in `QRCodeFormatter`
3. Update UI in `QRGeneratorTab`
4. Add to available types list in controller

#### New Export Format
1. Implement format support in `QRCodeGenerator`
2. Update save dialog in `QRGeneratorTab`
3. Add format options to settings

#### New Theme
1. Add theme colors to `ThemeManager`
2. Create stylesheet in `get_stylesheet` method
3. Update theme selection in UI

### Testing

#### Manual Testing
- Test all QR code types with various content
- Verify Excel import with different file formats
- Test QR reading with various image formats
- Validate settings persistence

#### Automated Testing
- Unit tests for core functionality
- Integration tests for UI components
- Performance tests for bulk operations

## License

This project is licensed under the MIT License. See LICENSE file for details.

## Support

For issues, questions, or contributions:
1. Check the troubleshooting section
2. Review the documentation
3. Create an issue with detailed information
4. Provide sample data for reproduction

## Version History

### v1.0.0
- Initial release
- Core QR generation functionality
- Excel bulk generation
- QR code reading
- Theme support
- Settings management
- Executable build support
