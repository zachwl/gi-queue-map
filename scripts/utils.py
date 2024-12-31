def standardizeFields(df, standard_columns, input_columns):
    # Create a mapping from standard_columns to input_columns using zip
    column_mapping = dict(zip(standard_columns, input_columns))
    
    # Subset the DataFrame to include only the input columns
    subset_columns = []

    # Loop through each standard column name
    for col in standard_columns:
        # Use the mapping to find the corresponding column name in the input DataFrame
        mapped_column = column_mapping[col]
        # Add the mapped column name to the list
        subset_columns.append(mapped_column)

    # Use the list of mapped column names to subset the DataFrame
    df_subset = df[subset_columns]  
    
    # Rename the columns to the standard column names
    df_subset.columns = standard_columns
    
    # Return the standardized DataFrame
    return df_subset

def standardizeFuels(projects, fuel_indices):
    for fuel, indices in fuel_indices.items():
        projects.loc[indices, 'fuel'] = fuel
    return projects