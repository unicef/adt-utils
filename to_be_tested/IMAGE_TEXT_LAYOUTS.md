# Image and Text Layout Standardization

## Overview

The `standardize_image_text_layouts.py` script standardizes the layout of images and text content across HTML files, creating responsive and visually balanced presentations based on the template from `9_0_adt.html`.

## Features

### Intelligent Layout Detection
The script analyzes the text-to-image ratio to intelligently choose the best layout strategy:

- **Image Top/Text Bottom** (`image_top_text_bottom`): For very short text content (ratio < 100)
- **Side-by-side** (`image_left_text_right`): For moderate text content (ratio 100-500)
- **Side-by-side** (`text_left_image_right`): For balanced text content (ratio 500-1000)
- **Text Top/Image Bottom** (`text_top_image_bottom`): For extensive text content (ratio > 1000)

### Responsive Design
All layouts are fully responsive using Tailwind CSS classes:
- **Mobile**: Vertical stacking for better readability
- **Desktop**: Side-by-side arrangements when appropriate
- **Tablet**: Flexible layouts that adapt to screen size

### Layout Strategies

#### 1. Side-by-side Layouts (Horizontal)
```html
<div class="flex flex-col lg:flex-row items-center justify-center gap-8">
  <div class="flex-1 w-full lg:w-1/2 flex flex-col justify-center">
    <!-- Text content -->
  </div>
  <div class="flex justify-center items-center w-full lg:w-1/2">
    <!-- Image content -->
  </div>
</div>
```

#### 2. Stacked Layouts (Vertical)
```html
<!-- Text first -->
<div class="space-y-4 mb-6">
  <!-- Text content -->
</div>
<!-- Then image -->
<div class="flex justify-center">
  <!-- Image content -->
</div>
```

### Content Preservation
- All `data-id` attributes are preserved
- Accessibility attributes maintained
- Image alt text and aria-labels kept intact
- Heading hierarchy preserved

## Usage

### Run on All Files
```bash
python3 standardize_image_text_layouts.py
```

### Integration with Master Script
The script is included in `standardize_all.py` as Step 4:
```bash
python3 standardize_all.py 6 58
```

## Algorithm Logic

### Text-to-Image Ratio Calculation
```python
def get_text_to_image_ratio(soup, section):
    # Count total text content length
    # Count number of images
    # Return ratio: text_length / num_images
```

### Layout Decision Tree
1. **No images** → `text_only`
2. **Ratio < 100** → `image_top_text_bottom` (minimal text, image-focused)
3. **Ratio 100-500** → `image_left_text_right` (moderate text, balanced)
4. **Ratio 500-1000** → `text_left_image_right` (more text, text-focused)
5. **Ratio > 1000** → `text_top_image_bottom` (extensive text, text-dominant)

## Examples from Processing

### Short Text (Image-focused)
- `58_0_adt.html`: Ratio 29.0 → `image_top_text_bottom`
- `10_0_adt.html`: Ratio 0.0 → `image_top_text_bottom`

### Moderate Text (Balanced)
- `30_0_adt.html`: Ratio 386.0 → `image_left_text_right`
- `33_0_adt.html`: Ratio 487.0 → `image_left_text_right`

### Longer Text (Text-focused)
- `16_0_adt.html`: Ratio 998.0 → `text_left_image_right`
- `36_0_adt.html`: Ratio 803.0 → `text_left_image_right`

### Extensive Text (Text-dominant)
- `19_0_adt.html`: Ratio 3262.0 → `text_top_image_bottom`
- `43_0_adt.html`: Ratio 4549.0 → `text_top_image_bottom`

## Template-Based Design

The script follows the design patterns from `9_0_adt.html`:
- Centered viewport with `min-h-screen`
- Consistent spacing with `gap-8`
- Responsive image sizing with `max-w-sm` or `max-w-md`
- Proper flex layouts for alignment

## CSS Classes Applied

### Container Classes
- `flex flex-col lg:flex-row` - Responsive direction
- `items-center justify-center` - Centering
- `gap-8` - Consistent spacing

### Image Classes
- `w-full max-w-sm rounded-lg shadow-md` - Responsive sizing with style
- `mx-auto` - Center alignment when needed

### Text Classes
- `flex-1 w-full lg:w-1/2` - Responsive width
- `flex flex-col justify-center` - Vertical alignment
- `space-y-4` - Consistent text spacing

## Compatibility

The script maintains full compatibility with:
- Existing data-id systems
- Accessibility attributes
- Previous standardization steps
- Tailwind CSS framework
- BeautifulSoup HTML parsing

## Files Processed

The script processes all HTML files in the `output/` directory except `index.html`, automatically detecting sections with images and applying the appropriate layout strategy based on content analysis.
