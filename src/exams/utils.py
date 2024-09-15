async def update_user_rating(user_rating: str) -> str:
    if user_rating == "A1":
        return "A2"
    elif user_rating == "A2":
        return "B1"
    elif user_rating == "B1":
        return "B2"
    elif user_rating == "B2":
        return "C1"
    elif user_rating == "C1":
        return "C2"
    elif user_rating == "C2":
        return "C2"
