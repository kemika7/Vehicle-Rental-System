export type Role = "admin" | "employee";

export interface LoginRequest {
  username: string; // FastAPI OAuth2PasswordRequestForm uses "username" field
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface EmployeeResponse {
  id: number;
  name: string;
  email: string;
  role: Role;
  office_id: number;
}

export interface RegisterRequest {
  name: string;
  email: string;
  password: string;
  office_id: number;
}
