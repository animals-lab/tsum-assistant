import { motion } from "framer-motion";
import { MessageIcon } from "./icons";

export const Overview = () => {
  return (
    <motion.div
      key="overview"
      className="max-w-3xl mx-auto md:mt-20"
      initial={{ opacity: 0, scale: 0.98 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.98 }}
      transition={{ delay: 0.5 }}
    >
      <div className="rounded-xl p-6 flex flex-col gap-8 leading-relaxed text-center max-w-xl">
        <p className="flex flex-row justify-center">
          <MessageIcon size={32} />
        </p>
        <p>
          Welcome to AI Chat! Ask me anything and I'll do my best to help you.
        </p>
      </div>
    </motion.div>
  );
};