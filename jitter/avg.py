import pandas as pd

def calculate_average_rtt(file_path):
    """
    Reads a CSV file with 'avg_rtt_ms' column and calculates the mean RTT.
    """
    try:
        # 1. Read the CSV file into a DataFrame
        df = pd.read_csv(file_path)
        
        # 2. Calculate the mean of the 'avg_rtt_ms' column
        average_rtt = df['avg_rtt_ms'].mean()
        
        # Display the result
        print(f"Successfully loaded data from {file_path}.")
        print(f"The total number of data points is: {len(df)}")
        print(f"The calculated Average RTT is: {average_rtt:.2f} ms")
        
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found. Please ensure the file is in the correct directory.")
    except KeyError:
        print("Error: The column 'avg_rtt_ms' was not found in the CSV file. Please check the column names.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

# Execute the function with your file name
calculate_average_rtt('results16/rtt.csv')