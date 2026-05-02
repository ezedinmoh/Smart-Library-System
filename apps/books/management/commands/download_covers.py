"""
Management command to download cover images for books
"""
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from apps.books.models import Book
import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO


class Command(BaseCommand):
    help = 'Download cover images for books that don\'t have them'

    def generate_cover(self, title, author, isbn):
        """Generate a simple cover image for books without covers"""
        # Create image with gradient background
        width, height = 400, 600
        img = Image.new('RGB', (width, height))
        
        # Create gradient background
        for y in range(height):
            # Gradient from dark blue to lighter blue
            r = int(44 + (y / height) * 30)
            g = int(62 + (y / height) * 40)
            b = int(80 + (y / height) * 50)
            for x in range(width):
                img.putpixel((x, y), (r, g, b))
        
        draw = ImageDraw.Draw(img)
        
        # Try multiple font options
        title_font = None
        author_font = None
        
        font_options = [
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/calibri.ttf",
            "C:/Windows/Fonts/segoeui.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "arial.ttf",
        ]
        
        for font_path in font_options:
            try:
                title_font = ImageFont.truetype(font_path, 36)
                author_font = ImageFont.truetype(font_path, 24)
                break
            except:
                continue
        
        # If no font found, use default
        if not title_font:
            title_font = ImageFont.load_default()
            author_font = ImageFont.load_default()
        
        # Wrap title text
        words = title.split()
        lines = []
        current_line = []
        max_width = width - 60
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            try:
                bbox = draw.textbbox((0, 0), test_line, font=title_font)
                text_width = bbox[2] - bbox[0]
            except:
                text_width = len(test_line) * 20
            
            if text_width > max_width and current_line:
                lines.append(' '.join(current_line))
                current_line = [word]
            else:
                current_line.append(word)
        
        if current_line:
            lines.append(' '.join(current_line))
        
        # Draw title with shadow
        y_offset = 180
        for line in lines[:4]:  # Max 4 lines
            try:
                bbox = draw.textbbox((0, 0), line, font=title_font)
                text_width = bbox[2] - bbox[0]
            except:
                text_width = len(line) * 20
            
            x = (width - text_width) // 2
            # Shadow
            draw.text((x + 2, y_offset + 2), line, fill='#000000', font=title_font)
            # Text
            draw.text((x, y_offset), line, fill='#FFFFFF', font=title_font)
            y_offset += 50
        
        # Draw author with shadow
        y_offset += 40
        try:
            bbox = draw.textbbox((0, 0), author, font=author_font)
            text_width = bbox[2] - bbox[0]
        except:
            text_width = len(author) * 12
        
        x = (width - text_width) // 2
        # Shadow
        draw.text((x + 2, y_offset + 2), author, fill='#000000', font=author_font)
        # Text
        draw.text((x, y_offset), author, fill='#E0E0E0', font=author_font)
        
        # Add decorative elements
        # Top border
        draw.rectangle([(20, 20), (width-20, 30)], fill='#FFFFFF')
        # Bottom border
        draw.rectangle([(20, height-30), (width-20, height-20)], fill='#FFFFFF')
        
        # Save to BytesIO
        buffer = BytesIO()
        img.save(buffer, format='JPEG', quality=90)
        buffer.seek(0)
        return buffer

    def handle(self, *args, **options):
        books_without_cover = Book.objects.filter(cover_image='')
        total = books_without_cover.count()
        
        self.stdout.write(f'Found {total} books without cover images')
        
        success = 0
        generated = 0
        failed = 0

        for book in books_without_cover:
            self.stdout.write(f'\nProcessing: {book.title}')
            
            try:
                # Try to download from Open Library
                cover_url = f'https://covers.openlibrary.org/b/isbn/{book.isbn}-L.jpg'
                self.stdout.write(f'  Trying Open Library: {cover_url}')
                
                response = requests.get(cover_url, timeout=10)
                if response.status_code == 200 and len(response.content) > 1000:
                    book.cover_image.save(
                        f'{book.isbn}.jpg',
                        ContentFile(response.content),
                        save=True
                    )
                    self.stdout.write(self.style.SUCCESS(f'  ✓ Cover downloaded from Open Library'))
                    success += 1
                else:
                    # Generate a cover
                    self.stdout.write(f'  Generating cover image...')
                    cover_buffer = self.generate_cover(book.title, book.author, book.isbn)
                    book.cover_image.save(
                        f'{book.isbn}.jpg',
                        ContentFile(cover_buffer.read()),
                        save=True
                    )
                    self.stdout.write(self.style.WARNING(f'  ✓ Generated cover image'))
                    generated += 1
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ✗ Error: {str(e)}'))
                failed += 1

        # Summary
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS(f'Downloaded: {success} covers'))
        self.stdout.write(self.style.WARNING(f'Generated: {generated} covers'))
        self.stdout.write(self.style.ERROR(f'Failed: {failed} covers'))
        self.stdout.write('='*60)
