import os
import time
import math
import argparse
from collections import namedtuple
from PIL import Image, ImageDraw

Point = namedtuple("Point", ['x', 'y'])

# RGB tuples.
BACKGROUND_COLOR = (0, 0, 0)
CELL_COLOR = (255, 0, 0)
PRIME_HIGHLIGHT_COLOR = (0, 255, 0)
NONPRIME_HIGHLIGHT_COLOR = (0, 255, 255)

# Set the array size when known.
is_prime = [True] * 42

def sieve(n):
    global is_prime
    is_prime = [True] * (n + 1)

    is_prime[0] = is_prime[1] = False
    end = math.ceil(math.sqrt(n))
    for p in range(2, end + 1):
        if not is_prime[p]:
            continue
        for i in range(p * p, n + 1, p):
            is_prime[i] = False

def dimension_to_level(dimension):
    return math.ceil((dimension + 1) / 2)

def level_to_dimension(level):
    return 2 * level - 1

def max_int(levels):
    return level_to_dimension(levels) ** 2

def int_to_level(n):
    return math.ceil(math.sqrt(n)) // 2

def int_to_point(n):
    """ Return the position of 'n' on the number spiral with its origin at n = 1. """

    level = int_to_level(n)
    sq = level_to_dimension(level)
    seg1 = sq * sq + 1
    seg2 = seg1 + 2 * level
    seg3 = seg2 + 2 * level
    seg4 = seg3 + 2 * level

    row = 0
    col = 0
    if n < seg2:
        row=-level + 1 + (n - seg1)
        col=level
    elif n < seg3:
        row=level
        col=level - 1 - (n - seg2)
    elif n < seg4:
        row=level - 1 - (n - seg3)
        col=-level
    else:
        row=-level
        col=-level + 1 + (n - seg4)

    return Point(x=col, y=row)

def local_to_screen(x, y, width, height, levels):
    """ Returns screen cell coordinates like so: [(x1, y1), (x2, y2)]. """

    # Note: I allow off by one pixel errors.
    # (x, y) coordinates that map to values off screen get ignored.

    a = min(width, height)

    # The remainder (cut) is used to center the image inside the square. This is done
    # so that each cell takes up the same amount of pixels and there aren't any nasty
    # rounding errors. If levels is too high, let each cell take up one pixel.
    unit, cut = divmod(a, level_to_dimension(levels))
    if unit == 0:
        unit = 1
        cut = 0
        levels = (a + 1) // 2 + 1

    top_left_x = (width - a + cut) // 2
    top_left_y = (height - a + cut) // 2

    x1 = unit * (x + levels - 1) + top_left_x
    y1 = unit * (levels - 1 - y) + top_left_y
    x2 = x1 + unit - 1
    y2 = y1 + unit - 1

    return [(x1, y1), (x2, y2)]

def draw_cell(n, img, draw, levels, color=CELL_COLOR):
    x, y = int_to_point(n)
    rect = local_to_screen(x, y, img.width, img.height, levels)
    draw.rectangle(rect, fill=color)

def append_to_image(img, start, end, levels, width, height, highlight=True):
    draw = ImageDraw.Draw(img)

    # Clear the first cell in case it was highlighted before.
    draw_cell(start, img, draw, levels, color=BACKGROUND_COLOR)

    for i in range(start, end):
        if is_prime[i]:
            draw_cell(i, img, draw, levels)

    # Highlight the last cell for an animation effect.
    highlight_color = CELL_COLOR
    if highlight:
        highlight_color = PRIME_HIGHLIGHT_COLOR if is_prime[end] else NONPRIME_HIGHLIGHT_COLOR
    if highlight or is_prime[end]:
        draw_cell(end, img, draw, levels, color=highlight_color)

    return img

def create_image(levels, width, height, n=-1, highlight=False):
    # Using Palette mode because this is for a GIF.
    img = Image.new("P", (width, height), BACKGROUND_COLOR)
    if n < 0:
        n = max_int(levels)
    append_to_image(img, 1, n, levels, width, height, highlight=highlight)
    return img

def create_gif(path, fps, width, height, levels, save_frames=False, primes_only=False):
    filename, ext = os.path.splitext(path)
    path_format = "{pre}{{}}.png".format(pre=filename)

    max_n = max_int(levels)

    last_frame = create_image(levels, width, height, n=1)
    frames = []
    prev = 1
    for i in range(1, max_n + 1):
        if i < max_n and primes_only and not is_prime[i]:
            continue

        last_frame = append_to_image(last_frame.copy(), prev, i, levels, width, height, highlight=(i < max_n))
        frames.append(last_frame)

        if save_frames:
            frames[-1].save(path_format.format(i))

        prev = i
        
    frames[0].save(path, 
                   format="GIF", 
                   save_all=True, 
                   append_images=frames[1:], 
                   duration=1000/fps, 
                   loop=1)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs='?', type=str, default="ulamspiral")
    parser.add_argument("--size", nargs=2, default=(420, 420), 
                        help="Width and height in pixels.")
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--dimension", type=int, default=21,
                        help="The grid dimension. Should be an odd number.")
    parser.add_argument("--max_size", action="store_true", 
                        help="Fit as many spirals as possible to the given image size.")
    parser.add_argument("--save_frames", action='store_true', 
                        help="Save every frame that makes up the GIF as a seperate image file.")
    parser.add_argument("--primes_only", action='store_true',
                        help="Animate only prime numbers in GIF mode.")
    parser.add_argument("--image_only", action='store_true', 
                        help="Only create an image, not a GIF.")
    args = parser.parse_args()

    t = time.time()
    
    # If levels is too high (so that each cell takes up less than one pixel),
    # then I clamp it, so that each cell has at least one pixel.
    width = int(args.size[0])
    height = int(args.size[1])
    levels = dimension_to_level(args.dimension)
    max_levels = (min(width, height) + 1) // 2 + 1
    if args.max_size or levels > max_levels:
        levels = max_levels

    sieve(max_int(levels))

    if args.image_only:
        path, ext = os.path.splitext(args.path)
        path = args.path if ext else "{}.png".format(path)
        create_image(levels, width, height).save(path)
    else:
        path, ext = os.path.splitext(args.path)
        path = args.path if ext else "{}.gif".format(path)

        create_gif(path, args.fps, width, height, levels, 
                   save_frames=args.save_frames, primes_only=args.primes_only)
    
    print("Done in {:.2f} seconds.".format(time.time() - t))
