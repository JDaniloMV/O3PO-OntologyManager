import Header from './Header';
import Navbar from './Navbar';
import Footer from './Footer';

const Layout = ({ children }) => {
  return (
    <>
      <Header />
      <Navbar />
      <main className="min-h-screen px-4">{children}</main>
      <Footer />
    </>
  );
};

export default Layout;
