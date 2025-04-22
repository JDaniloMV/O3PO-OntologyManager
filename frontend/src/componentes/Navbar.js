import React from 'react';
import './Navbar.css';
import { Link } from 'react-router-dom';

const Navbar = () => {
  return (
    <nav className="navbar">
      <h1>Moove Lab</h1>
      <ul>
        <li><Link to="/">Home</Link></li>
        <li><Link to="/about">Sobre Nós</Link></li>
        <li><Link to="/products">Produtos</Link></li>
        <li><Link to="/store">Loja</Link></li>
        <li><Link to="/blog">Blog</Link></li>
        <li><Link to="/contact">Fale Conosco</Link></li>
        <li><Link to="/policy">Política de Privacidade</Link></li>
      </ul>
    </nav>
  );
};

export default Navbar;
