#!/usr/bin/env python3
"""
Restore original structure for files that had their text content removed
"""

from bs4 import BeautifulSoup

def restore_9_0_structure():
    """Restore the original 9_0_adt.html structure"""
    
    # Original content from the attachment
    original_html = '''<html lang="es">

<head>
    <meta charset="utf-8" />
    <meta content="width=device-width, initial-scale=1" name="viewport" />
    <title></title>
    <link href="./content/tailwind_output.css" rel="stylesheet" />
    <script src="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.6.0/js/all.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
    <meta content="9_0" name="page-section-id" />
</head>

<body class="bg-white lg:p-5 md:p-5 sm:p-0 mb-12 font-sans text-lg">
    <div id="interface-container"></div>
    <div id="nav-container"></div>
    <div class="flex justify-center items-center min-h-screen">
        <div class="container mx-auto max-w-5xl bg-white rounded-lg lg:px-24 md:px-12 px-6 pt-12 pb-12" id="content">
            <section aria-labelledby="section-heading" data-id="sectioneli5-9-0"
                data-section-type="text_and_images" role="article">
                <div class="flex flex-row items-center justify-center gap-8">
                    <div class="flex-1 w-1/2 flex flex-col justify-center">
                        <header class="mb-6">
                            <h1 class="text-5xl font-bold mb-4 text-teal-500" data-id="text-9-1" id="text-9-1"></h1>
                        </header>
                        <p class="text-lg mb-6 text-left" data-id="text-9-2"></p>
                        <p class="italic text-left text-pink-700"></p>
                    </div>
                    <div class="flex justify-center items-center w-1/2"><img
                            alt="Imagen: Una ilustración de una persona regando símbolos de salud y bienestar sobre su cabeza, representando el autocuidado."
                            aria-label="Imagen: Una ilustración de una persona regando símbolos de salud y bienestar sobre su cabeza, representando el autocuidado."
                            class="w-full max-w-sm rounded-lg" data-aria-id="aria-9-0-0" data-id="img-9-1"
                            src="./images/9_img-9-1.png" tabindex="0" /></div>
                </div>
            </section>
        </div>
    </div>
    <script src="./assets/modules/state.js" type="module"></script>
    <script src="./assets/base.js" type="module"></script>
</body>

</html>'''
    
    # Write the restored file
    with open('output/9_0_adt.html', 'w', encoding='utf-8') as f:
        f.write(original_html)
    
    print("✓ Restored 9_0_adt.html to original structure")

def main():
    restore_9_0_structure()
    print("Template file restored!")

if __name__ == "__main__":
    main()
