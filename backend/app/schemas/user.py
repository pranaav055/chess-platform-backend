from pydantic import BaseModel, EmailStr

class UserRegisterRequest(BaseModel):
    username: str 
    email: EmailStr
    password: str

class UserLoginRequest(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr 
    is_active: bool 
    rating: int 

    model_config = {"from_attributes": True}

class TokenResponse(BaseModel):
    access_token: str 
    token_type: str 