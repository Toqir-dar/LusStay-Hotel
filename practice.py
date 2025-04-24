def process_data_without_context_manager():
    try:
        # Open a file without using a context manager
        file = open("important_data.txt", "r")
        
        # Process the contents
        data = file.read()
        processed_results = data.split('\n')
        
        # Let's say an error occurs during processing
        result = 10 / 0  # Deliberate ZeroDivisionError
        
        # This line never executes due to the exception
        file.close()
        
        return processed_results
    except ZeroDivisionError:
        print("Error: Division by zero!")
        # Oops! We forgot to close the file in the exception handler
        # The file remains open, potentially causing resource leaks
        
    # If we return from the function without closing the file:
    # 1. System resources remain tied up
    # 2. Changes might not be flushed to disk
    # 3. Other processes might be blocked from accessing the file
    return None

# The function will raise an exception, but the file remains open
process_data_without_context_manager()