import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from PIL import Image, ImageTk
import numpy as np
import random
import pygame
import cv2
from PIL import ImageDraw

image_width = 400
image_height = 400
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

pygame.mixer.init()
pygame.mixer.music.load("background_music.mp3")
pygame.mixer.music.play(-1)
population_size = 10
num_tournaments = 3
mutation_rate = 0.005
population = []
min_black_percentage = 0.2
max_black_percentage = 0.5
zoom_factor = 2
black_pixel_mutation_rate = 0.001
white_pixel_mutation_rate = 0.0001
zoom_factor = [1.0]
user_preferences = {
    'shape_complexity': 1,
    'symmetry': 1,
    'texture_richness': 1,
    'balance': 1
}
preferences_locked = False
shape_complexity_var = None
symmetry_var = None
texture_richness_var = None
balance_var = None


def apply_preferences():
  global user_preferences, shape_complexity_var, symmetry_var, texture_richness_var, balance_var, preferences_locked
  user_preferences['shape_complexity'] = shape_complexity_var.get()
  user_preferences['symmetry'] = symmetry_var.get()
  user_preferences['texture_richness'] = texture_richness_var.get()
  user_preferences['balance'] = balance_var.get()
  preferences_locked = True
  display_rating_screen()


def get_neighbors(image, x, y):
  neighbors = []
  for dx in range(-3, 4):
    for dy in range(-3, 4):
      nx, ny = x + dx, y + dy
      if 0 <= nx < image_height and 0 <= ny < image_width:
        neighbors.append(image[nx, ny])
  return neighbors


def adjust_symmetry(image, user_preferences):
  if user_preferences['symmetry'] == 1:
    return image  # No change
  elif user_preferences['symmetry'] == 2:
    return enforce_symmetry(image, 'horizontal')
  elif user_preferences['symmetry'] == 3:
    return enforce_symmetry(image, 'both')


def enforce_symmetry(image, mode):
  half_width = image_width // 2
  if mode == 'horizontal':
    image[:, half_width:] = image[:, half_width - 1::-1]
  elif mode == 'both':
    image[:, half_width:] = image[:, half_width - 1::-1]
    image[half_width:, :] = image[half_width - 1::-1, :]
  return image


def adjust_texture_richness(image, user_preferences):
  if user_preferences['texture_richness'] == 1:
    return image  # No change
  elif user_preferences['texture_richness'] == 2:
    return add_texture(image, 1.5)
  elif user_preferences['texture_richness'] == 3:
    return add_texture(image, 2.0)


def add_texture(image, factor):
  blurred = cv2.GaussianBlur(image, (5, 5), 0)
  return cv2.addWeighted(image, factor, blurred, 1 - factor, 0)


def adjust_shape_complexity(image, user_preferences):
  if user_preferences['shape_complexity'] == 1:
    return image  # No change
  elif user_preferences['shape_complexity'] == 2:
    return add_noise(image, 0.01)
  elif user_preferences['shape_complexity'] == 3:
    return add_noise(image, 0.02)


def add_noise(image, factor):
  noise = np.random.normal(0, factor * 255, image.shape)
  noisy_image = image + noise
  return np.clip(noisy_image, 0, 255).astype(np.uint8)


def adjust_balance(image, user_preferences):
  black_pixels = np.count_nonzero(image == 0)
  white_pixels = image_height * image_width - black_pixels

  target_black = int(black_pixels * user_preferences['balance'] / 3)
  target_white = image_height * image_width - target_black

  if black_pixels < target_black:
    image[np.random.rand(image_height, image_width) < (target_black -
                                                       black_pixels) /
          (image_height * image_width)] = 0
  elif black_pixels > target_black:
    image[np.random.rand(image_height, image_width) < (black_pixels -
                                                       target_black) /
          (image_height * image_width)] = 255

  return image


def calculate_crowding_distance(fitness_values):
  num_individuals = len(fitness_values)
  distances = [0] * num_individuals
  sorted_indices = sorted(range(num_individuals),
                          key=lambda i: fitness_values[i])

  distances[sorted_indices[0]] = float('inf')
  distances[sorted_indices[-1]] = float('inf')

  for i in range(1, num_individuals - 1):
    distances[sorted_indices[i]] = fitness_values[sorted_indices[
        i + 1]] - fitness_values[sorted_indices[i - 1]]

  return distances


def adjust_mutation_rate(ratings):
  diversity_factor = 1 / np.std(ratings) if np.std(ratings) != 0 else 1
  return mutation_rate * diversity_factor


def mutate_population(population, user_preferences):
  mutated_population = []
  for image in population:
    mutated_image = mutate_image1(image, user_preferences)

    mutated_image = adjust_symmetry(mutated_image, user_preferences)
    mutated_image = adjust_texture_richness(mutated_image, user_preferences)
    mutated_image = adjust_shape_complexity(mutated_image, user_preferences)
    mutated_image = adjust_balance(mutated_image, user_preferences)

    mutated_population.append(mutated_image)
  return mutated_population


def display_rating_screen():
  global preferences_locked
  if not preferences_locked:
    messagebox.showwarning("Preferences Not Set",
                           "Please set your preferences before proceeding.")
    return

  preferences_window.destroy()
  display_menu()


def create_pixel_art():
  for _ in range(population_size):
    image = np.random.randint(
        0, 2, (image_height, image_width), dtype=np.uint8) * 255
    population.append(image)


# def mutate_image1(image, user_preferences):
#   mutated_image = image.copy()
#   for i in range(image_height):
#     for j in range(image_width):
#       neighbors = get_neighbors(image, i, j)

#       if random.random() < (black_pixel_mutation_rate if image[i, j] == 0 else
#                             white_pixel_mutation_rate):
#         if should_form_line(neighbors) or should_form_shape(
#             neighbors) or should_form_pattern(neighbors):
#           mutated_image[i, j] = 0
#         else:
#           mutated_image[i, j] = random.choice([0, 255])
#       else:
#         majority_value = max(set(neighbors), key=neighbors.count)
#         mutated_image[i, j] = majority_value

#   return mutated_image


def mutate_image1(image, user_preferences):

  mutated_image = image.copy()

  for i in range(image_height):
    for j in range(image_width):
      neighbors = []
      for dx in range(-3, 4):
        for dy in range(-3, 4):
          x = i + dx
          y = j + dy
          if 0 <= x < image_height and 0 <= y < image_width:
            neighbors.append(image[x, y])

      if neighbors:
        if random.random() < (black_pixel_mutation_rate if image[i, j] == 0
                              else white_pixel_mutation_rate):
          if should_form_line(neighbors) or should_form_shape(
              neighbors) or should_form_pattern(
                  neighbors) or should_form_custom_shape(i, j, image):
            mutated_image[i, j] = 0
          else:
            mutated_image[i, j] = random.choice([0, 255])
        else:
          majority_value = max(set(neighbors), key=neighbors.count)
          mutated_image[i, j] = majority_value

  black_pixels = np.count_nonzero(mutated_image == 0)
  total_pixels = image_height * image_width
  black_percentage = black_pixels / total_pixels
  if black_percentage < min_black_percentage:
    mutated_image[np.random.rand(image_height, image_width) < (
        min_black_percentage - black_percentage)] = 0
  elif black_percentage > max_black_percentage:
    mutated_image[np.random.rand(image_height, image_width) < (
        black_percentage - max_black_percentage)] = 255

  return mutated_image


def generate_shapes(image):
  shapes = []
  for i in range(image_height):
    for j in range(image_width):
      if image[i, j] == 0:  # If pixel is black
        shape = find_shape(image, i, j)
        if shape:
          shapes.append(shape)
  return shapes


def find_shape(image, i, j):
  shape = set()
  stack = [(i, j)]
  while stack:
    x, y = stack.pop()
    if (x, y) not in shape and image[
        x, y] == 0:  # If pixel is black and not already part of shape
      shape.add((x, y))
      # Add neighboring pixels to the stack
      for dx in range(-1, 2):
        for dy in range(-1, 2):
          nx, ny = x + dx, y + dy
          if (0 <= nx < image_height and 0 <= ny < image_width
              and (nx, ny) not in shape):
            stack.append((nx, ny))
  if len(shape) > 1:  # Ensure shape contains more than one pixel
    return shape
  else:
    return None


def draw_shapes(image, shapes, filled=True):
  img = Image.fromarray(image, 'L')
  draw = ImageDraw.Draw(img)
  for shape in shapes:
    points = list(shape)
    if filled:
      draw.polygon(points, outline=255, fill=0)
    else:
      draw.polygon(points, outline=255)
  return np.array(img)


def should_form_line(neighbors):
  if len(neighbors) >= 49:
    if neighbors[24] == 0:
      row1 = all(pixel == 0 for pixel in neighbors[21:28])  # Horizontal line
      row2 = all(pixel == 0 for pixel in neighbors[3:46:7])  # Vertical line
      diag1 = all(pixel == 0 for pixel in [
          neighbors[16], neighbors[22], neighbors[28], neighbors[34]
      ])  # Diagonal \
      diag2 = all(pixel == 0 for pixel in [
          neighbors[18], neighbors[24], neighbors[30], neighbors[36]
      ])  # Diagonal /
      return any([row1, row2, diag1, diag2])
  return False


def should_form_shape(neighbors):
  if len(neighbors) == 49:
    if neighbors[24] == 0:  # Central pixel is black
      if all(pixel == 0 for pixel in neighbors[:9]):  # All neighbors are black
        return True
  return False


def generate_new_population(population, ratings, user_preferences,
                            crowding_distance):
  # sorted_indices = np.argsort(ratings)[::-1]
  sorted_indices = np.lexsort((crowding_distance, ratings))[::-1]

  selected_parents = [population[i] for i in sorted_indices[:4]]
  offspring = mutate_population(selected_parents, user_preferences)

  while len(offspring) < population_size - len(selected_parents):
    parent1, parent2 = random.choices(selected_parents, k=2)
    child1 = mutate_image1(parent1, user_preferences)
    child2 = mutate_image1(parent2, user_preferences)
    # child1 = mutate_image(parent1)
    # child2 = mutate_image(parent2)
    offspring.extend([child1, child2])
  new_population = selected_parents + offspring
  return new_population


def should_form_pattern(neighbors):
  if len(neighbors) >= 49:
    pattern = [1, 0, 1, 0, 1, 0, 1, 0, 1]
    if neighbors == pattern:
      return True
  return False


# Function to display preferences window
def display_preferences_window():
  global preferences_locked, preferences_window, shape_complexity_var, symmetry_var, texture_richness_var, balance_var
  if preferences_locked:
    messagebox.showwarning(
        "Preferences Locked",
        "Preferences are already locked. They cannot be changed.")
    return

  preferences_window = tk.Toplevel(window)
  preferences_window.title("Art Preferences")

  shape_complexity_var = tk.IntVar(value=1)
  symmetry_var = tk.IntVar(value=1)
  texture_richness_var = tk.IntVar(value=1)
  balance_var = tk.IntVar(value=1)

  tk.Label(preferences_window, text="Shape Complexity:").grid(row=0,
                                                              column=0,
                                                              sticky="w")
  tk.Checkbutton(preferences_window,
                 text="Low",
                 variable=shape_complexity_var,
                 onvalue=1,
                 offvalue=0).grid(row=0, column=1, sticky="w")
  tk.Checkbutton(preferences_window,
                 text="Medium",
                 variable=shape_complexity_var,
                 onvalue=2,
                 offvalue=0).grid(row=0, column=2, sticky="w")
  tk.Checkbutton(preferences_window,
                 text="High",
                 variable=shape_complexity_var,
                 onvalue=3,
                 offvalue=0).grid(row=0, column=3, sticky="w")

  tk.Label(preferences_window, text="Symmetry:").grid(row=1,
                                                      column=0,
                                                      sticky="w")
  tk.Checkbutton(preferences_window,
                 text="Low",
                 variable=symmetry_var,
                 onvalue=1,
                 offvalue=0).grid(row=1, column=1, sticky="w")
  tk.Checkbutton(preferences_window,
                 text="Medium",
                 variable=symmetry_var,
                 onvalue=2,
                 offvalue=0).grid(row=1, column=2, sticky="w")
  tk.Checkbutton(preferences_window,
                 text="High",
                 variable=symmetry_var,
                 onvalue=3,
                 offvalue=0).grid(row=1, column=3, sticky="w")

  tk.Label(preferences_window, text="Texture Richness:").grid(row=2,
                                                              column=0,
                                                              sticky="w")
  tk.Checkbutton(preferences_window,
                 text="Low",
                 variable=texture_richness_var,
                 onvalue=1,
                 offvalue=0).grid(row=2, column=1, sticky="w")
  tk.Checkbutton(preferences_window,
                 text="Medium",
                 variable=texture_richness_var,
                 onvalue=2,
                 offvalue=0).grid(row=2, column=2, sticky="w")
  tk.Checkbutton(preferences_window,
                 text="High",
                 variable=texture_richness_var,
                 onvalue=3,
                 offvalue=0).grid(row=2, column=3, sticky="w")

  tk.Label(preferences_window, text="Balance:").grid(row=3,
                                                     column=0,
                                                     sticky="w")
  tk.Checkbutton(preferences_window,
                 text="Low",
                 variable=balance_var,
                 onvalue=1,
                 offvalue=0).grid(row=3, column=1, sticky="w")
  tk.Checkbutton(preferences_window,
                 text="Medium",
                 variable=balance_var,
                 onvalue=2,
                 offvalue=0).grid(row=3, column=2, sticky="w")
  tk.Checkbutton(preferences_window,
                 text="High",
                 variable=balance_var,
                 onvalue=3,
                 offvalue=0).grid(row=3, column=3, sticky="w")

  tk.Button(preferences_window, text="Apply",
            command=apply_preferences).grid(row=4, columnspan=4, pady=10)


def display_wait_message():
  wait_label = tk.Label(window,
                        text="Please wait...",
                        font=("Arial", 14, "bold"),
                        fg="white",
                        bg="gray",
                        padx=10,
                        pady=5,
                        borderwidth=2,
                        relief=tk.GROOVE)
  wait_label.place(relx=0.5, rely=0.4, anchor=tk.CENTER)
  window.update_idletasks()
  return wait_label


def save_preferences():
  wait_popup = display_wait_message()
  window.update()

  window.after(2000, continue_save_preferences, wait_popup)


def continue_save_preferences(wait_popup):
  ratings = [4, 2, 3, 5, 1, 4, 3, 2, 5, 3]
  # generate_new_population(population, ratings)
  wait_popup.destroy()
  messagebox.showinfo("Preferences Saved", "Your preferences have been saved.")
  # display_menu()


def detect_shapes(image):
  gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
  blurred = cv2.GaussianBlur(gray, (5, 5), 0)
  _, threshold = cv2.threshold(blurred, 127, 255, cv2.THRESH_BINARY)

  contours, _ = cv2.findContours(threshold, cv2.RETR_EXTERNAL,
                                 cv2.CHAIN_APPROX_SIMPLE)

  shape_list = []
  for contour in contours:
    approx = cv2.approxPolyDP(contour, 0.04 * cv2.arcLength(contour, True),
                              True)
    if len(approx) == 3:
      shape_list.append("Triangle")
    elif len(approx) == 4:
      shape_list.append("Rectangle")
    elif len(approx) > 4:
      shape_list.append("Circle")
  return shape_list


# Start the process
create_pixel_art()

window = tk.Tk()
window.title("Pixel Art Generator")
window.geometry(f"{SCREEN_WIDTH}x{SCREEN_HEIGHT}")
window.resizable(True, True)

background_image = Image.open("background.jpg")
background_photo = ImageTk.PhotoImage(background_image)
background_label = tk.Label(window, image=background_photo)
background_label.place(x=0, y=0, relwidth=1, relheight=1)

welcome_label = tk.Label(window,
                         text="Welcome to Pixel Generator",
                         font=("Helvetica", 24))
welcome_label.pack(pady=20)


def next_screen():
  welcome_label.destroy()
  next_button.destroy()
  display_preferences_window()
  # display_menu()


next_button = tk.Button(window, text="Next", command=next_screen)
next_button.pack(pady=10)


def display_alert():
  messagebox.showinfo(
      "Iterations Completed",
      "All iterations completed. Moving to favorite image selection.")


def should_form_custom_shape(x, y, image):

  shape = random.choice(["Triangle", "Rectangle", "Circle"])
  if shape == "Triangle":
    return can_be_triangle(x, y, image)
  elif shape == "Rectangle":
    return can_be_rectangle(x, y, image)
  elif shape == "Circle":
    return can_be_circle(x, y, image)
  return False


def display_menu():
  menu = tk.Menu(window)
  window.config(menu=menu)

  file_menu = tk.Menu(menu)
  menu.add_cascade(label="Menu", menu=file_menu)
  file_menu.add_command(label="Start")
  file_menu.add_command(label="Exit", command=window.quit)

  sidebar_frame = tk.Frame(window, bg="white", width=200)
  sidebar_frame.pack(side=tk.RIGHT, fill=tk.Y)

  preferences_button = tk.Button(sidebar_frame,
                                 text="Preferences",
                                 command=display_preferences_window)
  preferences_button.pack(pady=10)

  # Rate Image Button
  rate_button = tk.Button(sidebar_frame,
                          text="Rate Image",
                          command=lambda: rate_image(rating_scale.get()))
  rate_button.pack(pady=10)

  zoom_in_button = tk.Button(sidebar_frame,
                             text="Zoom In",
                             command=lambda: zoom_image(zoom_factor, 2))
  zoom_in_button.pack(pady=5)
  zoom_out_button = tk.Button(sidebar_frame,
                              text="Zoom Out",
                              command=lambda: zoom_image(zoom_factor, 0.5))
  zoom_out_button.pack(pady=5)
  canvas = tk.Canvas(window, width=image_width, height=image_height)
  canvas.pack()

  highest_rated_mutations = []

  current_image_index = 0
  ratings = []
  generation = 1
  num_iterations = 8

  def remove_wait_message():
    for widget in window.winfo_children():
      if isinstance(widget,
                    tk.Label) and widget.cget("text") == "Please wait...":
        widget.destroy()

  def display_image(image):

    img = Image.fromarray(image, 'L')
    img = img.resize((int(image_width * zoom_factor[0]),
                      int(image_height * zoom_factor[0])))
    photo = ImageTk.PhotoImage(img)
    canvas.create_image(0, 0, anchor=tk.NW, image=photo)
    canvas.image = photo

  def zoom_image(zoom_factor_list, factor):
    zoom_factor_list[0] *= factor
    display_image(population[current_image_index])

  def rate_image(rating):
    global zoom_factor
    nonlocal current_image_index
    nonlocal ratings
    nonlocal generation
    nonlocal highest_rated_mutations

    ratings.append(rating)

    current_image_index = (current_image_index + 1) % len(population)

    if current_image_index == 0 and len(ratings) == population_size:
      fitness = calculate_fitness(ratings)
      crowding_distance = calculate_crowding_distance(ratings)

      print(f"Generation {generation} - Fitness: {fitness}")
      global mutation_rate
      mutation_rate = adjust_mutation_rate(ratings)
      display_wait_message()
      window.after(1000, remove_wait_message)
      highest_rated_image = population[0]
      highest_rated_mutations.append(highest_rated_image)

      population[:] = generate_new_population(population, ratings,
                                              user_preferences,
                                              crowding_distance)
      ratings.clear()
      generation += 1

      if generation > num_iterations:
        print("Process completed.")
        display_alert()
        generate_gif_animation(highest_rated_mutations)
        select_favorite_pixel_art(highest_rated_mutations)
        pygame.mixer.music.stop()
        if window:
          window.destroy()
      else:
        
        display_image(population[current_image_index])

    elif current_image_index != 0:
      display_image(population[current_image_index])

  rating_scale = tk.Scale(window,
                          from_=1,
                          to=5,
                          orient=tk.HORIZONTAL,
                          length=200)
  rating_scale.pack()
  rate_button = tk.Button(window,
                          text="Rate Image",
                          command=lambda: rate_image(rating_scale.get()))
  rate_button.pack()
  display_image(population[current_image_index])

  def calculate_fitness(ratings):
    return np.mean(ratings)

  def generate_gif_animation(images):
    frames = []
    for image in images:
      img = Image.fromarray(image, 'L').convert('RGB')
      frames.append(img)

    gif_path = "pixel_art_animation.gif"
    frames[0].save(gif_path,
                   save_all=True,
                   append_images=frames[1:],
                   optimize=False,
                   duration=200,
                   loop=0)
    print(f"Animation saved as {gif_path}")


def can_be_triangle(x, y, image):
  if x < image_height - 1 and y < image_width - 1:
    return image[x + 1, y] == image[x, y + 1] == image[x + 1, y + 1]
  return False


def can_be_rectangle(x, y, image):
  if x < image_height - 2 and y < image_width - 2:
    return image[x, y] == image[x + 1, y] == image[x, y + 1] == image[
        x + 1, y + 1] == image[x + 2, y] == image[x + 2, y + 1] == image[
            x, y + 2] == image[x + 1, y + 2] == image[x + 2, y + 2]
  return False


def can_be_circle(x, y, image):
  if x > 1 and x < image_height - 2 and y > 1 and y < image_width - 2:
    return image[x - 2, y - 1] == image[x - 2, y] == image[
        x - 2, y + 1] == image[x - 1, y - 2] == image[x - 1, y + 2] == image[
            x, y - 2] == image[x, y + 2] == image[x + 1, y - 2] == image[
                x + 1, y + 2] == image[x + 2, y -
                                       1] == image[x + 2, y] == image[x + 2,
                                                                      y + 1]
  return False


def select_favorite_pixel_art(images):

  def on_click(image):
    favorite_image_path = "favorite_pixel_art.png"
    Image.fromarray(image, 'L').save(favorite_image_path)
    print(f"Favorite pixel art saved as {favorite_image_path}")
    select_window.destroy()

  select_window = tk.Toplevel(window)
  select_window.title("These were your favourites across the generations.")

  canvas = tk.Canvas(select_window)
  canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

  scrollbar = tk.Scrollbar(select_window,
                           orient=tk.VERTICAL,
                           command=canvas.yview)
  scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

  canvas.configure(yscrollcommand=scrollbar.set)
  canvas.bind("<Configure>",
              lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

  frame = tk.Frame(canvas)
  canvas.create_window((0, 0), window=frame, anchor=tk.NW)

  for i, image in enumerate(images):
    img = Image.fromarray(image, 'L')
    img = img.resize((100, 100))
    photo = ImageTk.PhotoImage(img)

    button = tk.Button(frame,
                       image=photo,
                       command=lambda img=image: on_click(img))
    button.image = photo
    button.grid(row=i // 2, column=i % 2, padx=10, pady=10)

  select_window.mainloop()


def main():
  window.mainloop()


if __name__ == "__main__":
  main()
