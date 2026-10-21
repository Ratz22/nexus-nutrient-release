import { Routes, Route, useLocation } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import Nav from "./components/Nav";
import ChatDock from "./components/ChatDock";
import Predict from "./pages/Predict";
import Bench from "./pages/Bench";
import Simple from "./pages/Simple";

export default function App() {
  const location = useLocation();
  return (
    <>
      <Nav />
      <AnimatePresence mode="wait">
        <motion.div
          key={location.pathname}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.35, ease: [0.2, 0.7, 0.2, 1] }}
        >
          <Routes location={location}>
            <Route path="/" element={<Predict />} />
            <Route path="/bench" element={<Bench />} />
            <Route path="/fit" element={<Simple title="Fit" line="Bring your own lab data." />} />
            <Route path="/why" element={<Simple title="Why" line="The reasoning behind each prediction." />} />
            <Route path="/sources" element={<Simple title="Sources" line="Where the data comes from." />} />
          </Routes>
        </motion.div>
      </AnimatePresence>
      <ChatDock />
    </>
  );
}