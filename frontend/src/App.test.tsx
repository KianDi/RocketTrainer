import React from 'react';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import App from './App';

// Mock the AuthContext
jest.mock('./contexts/AuthContext', () => ({
  AuthProvider: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  useAuth: () => ({
    user: null,
    token: null,
    login: jest.fn(),
    logout: jest.fn(),
    loading: false
  })
}));

test('renders home page by default', () => {
  render(<App />);
  
  // Check if the main navigation elements are present
  expect(screen.getByText('RocketTrainer')).toBeInTheDocument();
  expect(screen.getByText('Level Up Your')).toBeInTheDocument();
});
