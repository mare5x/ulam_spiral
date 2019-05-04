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

# A flag for the local_to_screen function.
LOCAL_TO_SCREEN_ROUNDING = "DISCRETE"  # or "NONE"

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

def local_to_screen_none(x, y, width, height, levels):
    # Version that makes rounding errors but doesn't make a black border.
    
    a = min(width, height)
    dim = level_to_dimension(levels)

    unit = a / dim

    center_x = (width - unit) // 2
    center_y = (height - unit) // 2

    x1 = unit * x + center_x
    y1 = center_y - unit * y
    x2 = x1 + unit - 1
    y2 = y1 + unit - 1

    return [(x1, y1), (x2, y2)]

def local_to_screen_discrete(x, y, width, height, levels):
    # Note: I allow off by one pixel errors.
    # (x, y) coordinates that map to values off screen get ignored.

    # The remainder (cut) is used to center the image inside the square. This is done
    # so that each cell takes up the same amount of pixels and there aren't any nasty
    # rounding errors. If levels is too high, let each cell take up one pixel.
    
    a = min(width, height)
    dim = level_to_dimension(levels)
    unit, cut = divmod(a, dim)
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

def local_to_screen(x, y, width, height, levels):
    """ Returns screen cell coordinates like so: [(x1, y1), (x2, y2)]. """
    if LOCAL_TO_SCREEN_ROUNDING == "NONE":
        return local_to_screen_none(x, y, width, height, levels)
    return local_to_screen_discrete(x, y, width, height, levels)

def draw_cell(n, img, draw, levels, color=CELL_COLOR):
    x, y = int_to_point(n)
    rect = local_to_screen(x, y, img.width, img.height, levels)
    draw.rectangle(rect, fill=color)

def append_to_image(img, start, end, levels, width, height, highlight=False):
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

def create_spiral_frames(width, height, levels, primes_only=False):
    """ Create an animation that spirals outwards, a number at a time.
        
        Returns a list of PIL.Image.Image instances with an extra attribute <idx>. 
    """
    max_n = max_int(levels)
    last_frame = create_image(levels, width, height, n=1)
    frames = []
    prev = 1
    for i in range(1, max_n + 1):
        if i < max_n and primes_only and not is_prime[i]:
            continue

        last_frame = append_to_image(last_frame.copy(), prev, i, levels, width, height, highlight=(i < max_n))
        last_frame.idx = i
        frames.append(last_frame)
        prev = i

    return frames

def create_expand_frames(width, height, levels):
    """ Create an animation that expands outwards, a level at a time.
        
        Returns a list of PIL.Image.Image instances with an extra attribute <idx>. 
    """
    last_frame = create_image(levels, width, height, n=1)
    frames = []
    prev = 0
    for level in range(1, levels + 1):
        n = max_int(level)
        last_frame = append_to_image(last_frame.copy(), prev + 1, n, levels, width, height, highlight=False)
        last_frame.idx = level
        frames.append(last_frame)
        prev = n
    
    return frames

def create_grow_frames(width, height, levels):
    """ Create an animation that grows outwards, a level at a time.
        
        Returns a list of PIL.Image.Image instances with an extra attribute <idx>. 
    """
    frames = []
    for level in range(1, levels + 1):
        frame = create_image(level, width, height)
        frame.idx = level
        frames.append(frame)
    return frames

def save_all_frames(path, frames):
    filename, ext = os.path.splitext(path)
    path_format = "{pre}{{}}.png".format(pre=filename)
    for frame in frames:
        frame.save(path_format.format(frame.idx))

def save_gif(path, fps, frames):
    frames[0].save(path, 
        format="GIF", 
        save_all=True, 
        append_images=frames[1:], 
        duration=1000/fps, 
        loop=1)

def create_spiral_gif(path, fps, width, height, levels, save_frames=False, primes_only=False):
    frames = create_spiral_frames(width, height, levels, primes_only=primes_only)
    if save_frames:
        save_all_frames(path, frames)
    save_gif(path, fps, frames)

def create_expand_gif(path, fps, width, height, levels, save_frames=False):
    frames = create_expand_frames(width, height, levels)
    if save_frames:
        save_all_frames(path, frames)
    save_gif(path, fps, frames)

def create_grow_gif(path, fps, width, height, levels, save_frames=False):
    # A workaround to get a smoother animation.
    global LOCAL_TO_SCREEN_ROUNDING
    old_rounding = LOCAL_TO_SCREEN_ROUNDING
    LOCAL_TO_SCREEN_ROUNDING = "NONE"

    frames = create_grow_frames(width, height, levels)
    if save_frames:
        save_all_frames(path, frames)
    save_gif(path, fps, frames)
    
    LOCAL_TO_SCREEN_ROUNDING = old_rounding

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
                        help="Animate only prime numbers in Spiral GIF mode.")
    parser.add_argument("--image", action='store_true', 
                        help="Create a seperate image of the final spiral.")
    parser.add_argument("--spiral", action='store_true',
                        help="Create a Spiral GIF.")
    parser.add_argument("--expand", action='store_true',
                        help="Create an Expand GIF.")
    parser.add_argument("--grow", action='store_true',
                        help="Create a Grow GIF.")
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

    if args.image:
        path = "{}_image.png".format(args.path)
        create_image(levels, width, height).save(path)
        print(path)

    if args.spiral:
        path = "{}_spiral.gif".format(args.path)
        create_spiral_gif(path, args.fps, width, height, levels, 
                    save_frames=args.save_frames, primes_only=args.primes_only)
        print(path)

    if args.expand:
        path = "{}_expand.gif".format(args.path)
        create_expand_gif(path, args.fps, width, height, levels,
                    save_frames=args.save_frames)
        print(path)
    
    if args.grow:
        path = "{}_grow.gif".format(args.path)
        create_grow_gif(path, args.fps, width, height, levels, 
                    save_frames=args.save_frames)
        print(path)
    
    print("Done in {:.2f} seconds.".format(time.time() - t))
