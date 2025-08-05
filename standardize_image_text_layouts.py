#!/usr/bin/env python3
"""
Script to standardize image and text layouts using 9_0_adt.html as a template.
This script intelligently arranges image and text content in responsive
layouts.
"""

import os
from bs4 import BeautifulSoup


def get_text_to_image_ratio(soup, section):
    """Calculate the ratio of text content to images to help decide layout."""
    # Get all text content (excluding alt text and captions)
    text_elements = section.find_all([
        'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'span', 'div'
    ])
    total_text_length = 0
    element_count = 0
    
    for elem in text_elements:
        # Skip image containers and captions
        elem_classes = elem.get('class', [])
        has_caption = any('caption' in str(cls) for cls in elem_classes)
        if 'img' in str(elem) or (elem.get('class') and has_caption):
            continue
        
        text_content = elem.get_text(strip=True)
        data_id = elem.get('data-id', '')
        
        if text_content:
            total_text_length += len(text_content)
        elif data_id:
            # Empty elements with data-id are likely populated by JS
            # Assume moderate text content for layout decisions
            element_count += 1
    
    # Count images
    images = section.find_all('img')
    num_images = len(images)
    
    if num_images == 0:
        return float('inf')  # Only text, no images
    
    # If we have empty data-id elements, estimate text content
    if element_count > 0 and total_text_length == 0:
        # Estimate 200 characters per data-id element for layout decisions
        estimated_text = element_count * 200
        return estimated_text / num_images
    
    return total_text_length / num_images


def extract_content_elements(section):
    """Extract and categorize content elements from a section."""
    images = []
    text_content = []
    headings = []
    
    # Find all images and their containers
    for img in section.find_all('img'):
        img_container = img.find_parent(['figure', 'div']) or img
        images.append({
            'element': img,
            'container': img_container,
            'alt': img.get('alt', ''),
            'src': img.get('src', ''),
            'data_id': img.get('data-id', ''),
            'classes': img.get('class', [])
        })
    
    # Find headings (excluding the main h1 which should stay at top)
    for heading in section.find_all(['h2', 'h3', 'h4', 'h5', 'h6']):
        headings.append({
            'element': heading,
            'level': heading.name,
            'text': heading.get_text(strip=True),
            'data_id': heading.get('data-id', ''),
            'classes': heading.get('class', [])
        })
    
    # Find text content (paragraphs and other text containers)
    for elem in section.find_all(['p', 'div']):
        # Skip if it contains an image or is an image container
        is_img_container = any(
            img_info['container'] == elem for img_info in images
        )
        if elem.find('img') or is_img_container:
            continue
        
        # Get text content and data-id
        text = elem.get_text(strip=True)
        data_id = elem.get('data-id', '')
        
        # Include elements if they have text OR if they have data-id
        # (empty data-id elements are likely populated by JavaScript)
        if text or data_id:
            text_content.append({
                'element': elem,
                'text': text,
                'data_id': data_id,
                'classes': elem.get('class', [])
            })
    
    return images, text_content, headings


def choose_layout_strategy(images, text_content, text_to_image_ratio):
    """Choose the best layout strategy based on content analysis."""
    num_images = len(images)
    
    # If no images, return text-only
    if num_images == 0:
        return 'text_only'
    
    # If very short text (like captions), put image on top
    if text_to_image_ratio < 100:
        return 'image_top_text_bottom'
    
    # If moderate text amount, use side-by-side
    if text_to_image_ratio < 500:
        # Decide left/right based on content flow or reading pattern
        # Default to image left for better reading flow
        return 'image_left_text_right'
    
    # If lots of text, put text first then image
    if text_to_image_ratio > 1000:
        return 'text_top_image_bottom'
    
    # Default to side-by-side with text left (more natural reading flow)
    return 'text_left_image_right'


def create_standardized_layout(soup, section, images, text_content,
                               headings, strategy):
    """Create a standardized layout based on the chosen strategy."""
    
    # Clear existing content except main h1
    main_h1 = section.find('h1')
    section.clear()
    
    if main_h1:
        section.append(main_h1)
    
    if strategy == 'text_only':
        # Just add text content
        for heading in headings:
            section.append(heading['element'])
        for text in text_content:
            section.append(text['element'])
        return
    
    # Create the layout container
    if strategy == 'image_top_text_bottom':
        create_vertical_layout(
            soup, section, images, text_content, headings, image_first=True
        )
    elif strategy == 'text_top_image_bottom':
        create_vertical_layout(
            soup, section, images, text_content, headings, image_first=False
        )
    elif strategy == 'image_left_text_right':
        create_horizontal_layout(
            soup, section, images, text_content, headings, image_left=True
        )
    elif strategy == 'text_left_image_right':
        create_horizontal_layout(
            soup, section, images, text_content, headings, image_left=False
        )


def create_vertical_layout(soup, section, images, text_content, headings,
                           image_first=True):
    """Create a vertical layout (stacked) with responsive design."""
    
    if image_first:
        # Add images first
        for img_info in images:
            img_container = soup.new_tag(
                'div', **{'class': 'flex justify-center mb-6'}
            )
            
            # Create responsive image
            img = img_info['element']
            img['class'] = [
                'w-full', 'max-w-md', 'mx-auto', 'rounded-lg', 'shadow-md'
            ]
            
            img_container.append(img)
            section.append(img_container)
        
        # Add text content
        text_container = soup.new_tag('div', **{'class': 'space-y-4'})
        for heading in headings:
            text_container.append(heading['element'])
        for text in text_content:
            text_container.append(text['element'])
        section.append(text_container)
    else:
        # Add text first, then images
        text_container = soup.new_tag('div', **{'class': 'space-y-4 mb-6'})
        for heading in headings:
            text_container.append(heading['element'])
        for text in text_content:
            text_container.append(text['element'])
        section.append(text_container)
        
        for img_info in images:
            img_container = soup.new_tag(
                'div', **{'class': 'flex justify-center'}
            )
            
            img = img_info['element']
            img['class'] = [
                'w-full', 'max-w-md', 'mx-auto', 'rounded-lg', 'shadow-md'
            ]
            
            img_container.append(img)
            section.append(img_container)


def create_horizontal_layout(soup, section, images, text_content, headings,
                             image_left=True):
    """Create a horizontal layout (side-by-side) with responsive design."""
    
    # Create the main flex container
    # responsive: vertical on mobile, horizontal on desktop
    main_container = soup.new_tag('div', **{
        'class': [
            'flex', 'flex-col', 'lg:flex-row', 'items-center',
            'justify-center', 'gap-8'
        ]
    })
    
    # Create text container
    text_container = soup.new_tag('div', **{
        'class': [
            'flex-1', 'w-full', 'lg:w-1/2', 'flex', 'flex-col',
            'justify-center'
        ]
    })
    
    # Add headings and text to text container
    for heading in headings:
        text_container.append(heading['element'])
    for text in text_content:
        text_container.append(text['element'])
    
    # Create image container
    image_container = soup.new_tag('div', **{
        'class': [
            'flex', 'justify-center', 'items-center', 'w-full', 'lg:w-1/2'
        ]
    })
    
    # Add images to image container
    for img_info in images:
        img = img_info['element']
        img['class'] = ['w-full', 'max-w-sm', 'rounded-lg', 'shadow-md']
        image_container.append(img)
    
    # Arrange containers based on strategy
    if image_left:
        main_container.append(image_container)
        main_container.append(text_container)
    else:
        main_container.append(text_container)
        main_container.append(image_container)
    
    section.append(main_container)


def standardize_image_text_layout(file_path):
    """Standardize the image and text layout in an HTML file."""
    
    print(f"Processing: {file_path}")
    
    # Read the file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    soup = BeautifulSoup(content, 'html.parser')
    
    # Find sections with images
    sections = soup.find_all('section')
    
    for section in sections:
        # Check if section has images
        if not section.find('img'):
            section_id = section.get('data-id', 'unknown')
            print(f"  - Section {section_id} has no images, skipping")
            continue
            
        print(f"  - Processing section: {section.get('data-id', 'unknown')}")
        
        # Extract content elements
        images, text_content, headings = extract_content_elements(section)
        
        if not images:
            continue
            
        # Calculate text to image ratio
        text_to_image_ratio = get_text_to_image_ratio(soup, section)
        print(f"    Text to image ratio: {text_to_image_ratio:.1f}")
        
        # Choose layout strategy
        strategy = choose_layout_strategy(
            images, text_content, text_to_image_ratio
        )
        print(f"    Chosen strategy: {strategy}")
        
        # Apply the standardized layout
        create_standardized_layout(
            soup, section, images, text_content, headings, strategy
        )
        
        # Update section attributes for consistency
        section_type = 'text_and_images' if images else 'text_only'
        section['data-section-type'] = section_type
    
    # Add centered viewport styling to body if not present
    # (following 9_0_adt.html template)
    content_div = soup.find('div', id='content')
    if content_div and 'min-h-screen' not in str(content_div.get('class', [])):
        # Wrap content in centered viewport container
        parent_div = content_div.parent
        if parent_div and parent_div.name == 'body':
            # Remove content div from body
            content_div.extract()
            
            # Create centered container
            centered_container = soup.new_tag('div', **{
                'class': [
                    'flex', 'justify-center', 'items-center', 'min-h-screen'
                ]
            })
            centered_container.append(content_div)
            
            # Insert before scripts
            scripts = parent_div.find_all('script')
            if scripts:
                scripts[0].insert_before(centered_container)
            else:
                parent_div.append(centered_container)
    
    # Write the standardized file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(str(soup))
    
    print(f"  ✓ Completed: {file_path}")


def main():
    """Main function to process all HTML files in the output directory."""
    
    output_dir = "output"
    
    if not os.path.exists(output_dir):
        print(f"Error: {output_dir} directory not found!")
        return
    
    # Get all HTML files
    html_files = [
        f for f in os.listdir(output_dir)
        if f.endswith('.html') and f != 'index.html'
    ]
    html_files.sort()
    
    print(f"Found {len(html_files)} HTML files to process")
    print("=" * 60)
    
    for html_file in html_files:
        file_path = os.path.join(output_dir, html_file)
        try:
            standardize_image_text_layout(file_path)
        except Exception as e:
            print(f"  ✗ Error processing {html_file}: {str(e)}")
    
    print("=" * 60)
    print("Image and text layout standardization completed!")


if __name__ == "__main__":
    main()
