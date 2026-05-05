class StandardResponse:
    @staticmethod
    def success_response(data):
        return {"success": True, "data": data, "error": None}

    @staticmethod
    def error_response(message: str):
        return {"success": False, "data": None, "error": message}
