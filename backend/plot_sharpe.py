import matplotlib.pyplot as plt
import numpy as np

def create_data_matrix(csv_ref, col_index):
    data = np.zeros((3, 3))
    for i in range(0, 3):
        for j in range(0, 3):
            data[i][j] = float(csv_ref[i * 3 + j][col_index])
    return data

if __name__ == "__main__":
    # Open the CSV file and obtain only the lines with a lookback value of 100
    csv_file = open("output.csv", "r").readlines()
    csv_ref = [c.strip().split(",") for c in csv_file if c[:3] == "100"]
    
    # Create the data matrix from the CSV reference
    data = create_data_matrix(csv_ref, 5)
    
    # Create a plot
    fig, ax = plt.subplots()
    
    # Create a heatmap
    heatmap = ax.pcolor(data, cmap=plt.cm.Blues)
    
    # Labels for rows and columns
    row_labels = [0.5, 1.0, 1.5]
    column_labels = [2.0, 3.0, 4.0]
    
    # Annotate the heatmap with data values
    for y in range(data.shape[0]):
        for x in range(data.shape[1]):
            plt.text(x + 0.5, y + 0.5, '%.2f' % data[y, x],
                     horizontalalignment='center',
                     verticalalignment='center')

    # Add a colorbar
    plt.colorbar(heatmap)
    
    # Set ticks and labels for the axes
    ax.set_xticks(np.arange(data.shape[0]) + 0.5, minor=False)
    ax.set_yticks(np.arange(data.shape[1]) + 0.5, minor=False)
    ax.set_xticklabels(row_labels, minor=False)
    ax.set_yticklabels(column_labels, minor=False)
    
    # Set the title and labels for the axes
    plt.suptitle('Sharpe Ratio Heatmap', fontsize=18)
    plt.xlabel('Z-Score Exit Threshold', fontsize=14)
    plt.ylabel('Z-Score Entry Threshold', fontsize=14)
    
    # Show the plot
    plt.show()
