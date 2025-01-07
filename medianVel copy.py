import os
import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import find_peaks
plt.rcParams['font.family'] = 'Times New Roman'

def read_yolo_file(file_path):
    """Read YOLO formatted file and return a list of y-centers."""
    y_centers = []
    with open(file_path, 'r') as file:
        lines = file.readlines()
        for line in lines:
            parts = line.strip().split()
            y_center = float(parts[2])  # The third element is the y-center
            y_centers.append(y_center)
            # print(y_center)
    return y_centers

def find_peaks_and_troughs(y_centers):
    """Find and plot peaks and troughs in y-center data, ensuring the first and last data points are treated as specified."""
    # Convert list to numpy array for processing
    y = np.array(y_centers) * 512  # Scaling to pixel values
    t = np.arange(len(y_centers))  # Time indices

    # Finding peaks and troughs
    peaks, _ = find_peaks(y, distance=100, prominence=100)
    troughs, _ = find_peaks(-y, distance=100, prominence=100)

    # Enforce the first and last frame conditions
    # First frame is always a min
    if 0 not in troughs:
        troughs = np.append([0], troughs)

    # Last frame is opposite of the last detected peak or trough
    if len(peaks) > 0 and len(troughs) > 0:
        if peaks[-1] > troughs[-1]:  # Last detected was a peak
            if len(y) - 1 not in troughs:
                troughs = np.append(troughs, [len(y) - 1])
        else:  # Last detected was a trough
            if len(y) - 1 not in peaks:
                peaks = np.append(peaks, [len(y) - 1])

    # Create lists of tuples for peaks and troughs
    peak_points = [(t[index], y[index]) for index in peaks]
    trough_points = [(t[index], y[index]) for index in troughs]

    print("Peaks:", peak_points)
    print("Troughs:", trough_points)
    find_slopes(peak_points, trough_points)

    # Plotting
    plt.figure(figsize=(10, 5))
    plt.plot(t, y, label='Y-Center Data', color='black')
    plt.plot(t[peaks], y[peaks], 'x', label='Peaks', color='blue')
    plt.plot(t[troughs], y[troughs], 'bo', label='Troughs')
    plt.title('Detected Peaks and Troughs in Y-Center Data')
    plt.xlabel('Frame Index')
    plt.ylabel('Y-Center Value')
    plt.legend()
    plt.grid(True)
    plt.gca().invert_yaxis()  # Invert the y-axis
    plt.show()
    
def find_slopes(peaks, troughs):
    points = sorted(peaks + troughs, key=lambda x: x[0])
    print("Combined sorted points (x, y):", points)

    # Calculate slopes between consecutive points
    positive_slopes = []
    negative_slopes = []
    for i in range(1, len(points)):
        x1, y1 = points[i - 1]
        x2, y2 = points[i]
        # Calculate slope (delta_y / delta_x)
        if x2 != x1:  # Prevent division by zero
            slope = (y2 - y1) / (x2 - x1)
            if slope > 0:
                positive_slopes.append(slope)
            else:
                negative_slopes.append(slope)
        else:
            print("Vertical line detected, slope considered as infinite.")

    # Print the calculated slopes
    print("Positive slopes:")
    for index, slope in enumerate(positive_slopes):
        print(f"Slope {index + 1}: {slope}")
    print("Negative slopes:")
    for index, slope in enumerate(negative_slopes):
        print(f"Slope {index + 1}: {slope}")

    # Calculate the median slopes
    neg_slope_median = np.median(negative_slopes) if negative_slopes else 0
    pos_slope_median = np.median(positive_slopes) if positive_slopes else 0
    print('Negative slope median: (px/frame) ', neg_slope_median)
    print('Positive slope median: (px/frame) ', pos_slope_median)

    convert_to_mm_per_sec(neg_slope_median, pos_slope_median, 30, 414.20)

def convert_to_mm_per_sec(negative, positive, fps, calibration):
    negative = np.divide(np.multiply(negative, fps), calibration)
    positive = np.divide(np.multiply(positive, fps), calibration)
    print('Converted, vu: (mm/s)', negative)
    print('Converted vd: (mm/s)', positive)
    negative = negative * .001
    positive = positive * .001
    return negative, positive

def main(directory_path):
    """Main function to read files and plot y-centers."""
    y_centers_all_frames = []

    files = sorted(os.listdir(directory_path))

    for file_name in files:
        if file_name.endswith('.txt'):
            file_path = os.path.join(directory_path, file_name)
            y_centers = read_yolo_file(file_path)
            # Append all y-centers from each file to a single list
            y_centers_all_frames.extend(y_centers)

    find_peaks_and_troughs(y_centers_all_frames)

# Example usage:
directory_path = '/Users/calebchristian/Desktop/2024-07-02 10-42-43Lbl'
main(directory_path)