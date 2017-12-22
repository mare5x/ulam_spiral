from PIL import Image, ImageDraw


def get_spiral_width(spiral):
    return spiral * 2 - 1


WIDTH = 1800
HEIGHT = 1800

SPIRALS = 1024
     
N = get_spiral_width(SPIRALS)
RECT_PX = min(WIDTH, HEIGHT) / N


primes_marked = [False] * (N * N + 1)


def generate_primes():
    """ Sieve of Eratosthenes. """
    global primes_marked

    done = False
    p = 2
    while not done:
        for i in range(p + p, len(primes_marked), p):
            primes_marked[i] = True

        prev_p = p
        for i in range(p + 1, len(primes_marked)):
            if not primes_marked[i]:
                p = i
                break

        if (p == prev_p):
            done = True


def is_prime(a):
    return not primes_marked[a]


def paint_prime(draw, col, row):
    x = col * RECT_PX
    y = row * RECT_PX
    draw.ellipse((x, y, x + RECT_PX, y + RECT_PX), fill=(255, 0, 0))
    #draw.rectangle((x, y, x + RECT_PX, y + RECT_PX), fill=(255, 0, 0))


def write_spiral(path):
    image = Image.new("RGB", (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(image)

    for spiral in range(2, SPIRALS + 1):
        n = get_spiral_width(spiral)
        bottom_right = n * n
        bottom_left = bottom_right - (n - 1)
        top_left = bottom_left - (n - 1)
        top_right = top_left - (n - 1)

        left_edge_col = N // 2 - (spiral - 1)
        for i in range(2 * n + (n - 2) * 2):
            a = bottom_right - i
            if is_prime(a):
                col = -1
                row = -1
                if a >= bottom_left:
                    col = left_edge_col + (a - bottom_left)
                    row = left_edge_col + (n - 1)
                elif a >= top_left:
                    col = left_edge_col
                    row = left_edge_col + (a - top_left)
                elif a >= top_right:
                    col = left_edge_col + (top_left - a)
                    row = left_edge_col
                else:
                    col = left_edge_col + (n - 1)
                    row = left_edge_col + (top_right - a)
                paint_prime(draw, col, row)

    image.save(path)


if __name__ == "__main__":
    generate_primes()
    write_spiral("spiral.jpg")