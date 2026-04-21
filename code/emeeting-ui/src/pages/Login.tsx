// src/pages/Login.tsx
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { login } from '../api/auth';
import { useAuthStore } from '../store/authStore';

const Login = () => {
  const [email, setEmail] = useState('demo1@example.com');
  const [password, setPassword] = useState('demo1pass');
  const navigate = useNavigate();
  const { setAuth } = useAuthStore();

  const submit = async () => {
    try {
      const user = await login(email, password);
      setAuth(user);
      // TODO: перейти на cookie-based auth (HttpOnly) вместо хранения только в state.
      navigate('/');
    } catch (error) {
      console.error(error);
    }
  };

  return (
    <div className="container">
      <header>
        <h1>Вход в EMeeting</h1>
      </header>
      <form>
        <div className="form-group">
          <label>Email</label>
          <input type="email" autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} />
        </div>
        <div className="form-group">
          <label>Пароль</label>
          <input
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>
        <button className="primary-btn" type="button" onClick={submit}>Войти</button>
      </form>
    </div>
  );
};

export default Login;