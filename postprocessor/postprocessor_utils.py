# /postprocessor/postprocessor_utils.py

class PostProcessingUtils:
    @staticmethod
    def fill_missing_values(element):
        for key, value in element.items():
            if value is None:
                element[key] = None  # Set missing fields to null if not provided
        return element
