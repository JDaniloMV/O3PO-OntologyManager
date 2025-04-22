import React from 'react';
import './Header.css';

const Header = () => {
  return (
    <header className="site-header">
      <div className="logo">
        <img src="/images/logo.svg" alt="Logo Moove Lab" />
        <span className="slogan">Inovando com você</span>
      </div>
    </header>
  );
};

export default Header;

