import { type FormEvent, useState } from "react";
import { useAuth } from "./useAuth";

export function useLoginForm() {
  const { loading, error, login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    void login({ username: email, password });
  };

  return { email, setEmail, password, setPassword, loading, error, handleSubmit };
}
