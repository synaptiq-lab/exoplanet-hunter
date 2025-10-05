"use client";

import * as React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown } from "lucide-react";

export type MegaMenuItem = {
  id: number;
  label: string;
  subMenus?: {
    title: string;
    items: {
      label: string;
      description: string;
      icon: React.ElementType;
    }[];
  }[];
  link?: string;
};

export interface MegaMenuProps extends React.HTMLAttributes<HTMLUListElement> {
  items: MegaMenuItem[];
  className?: string;
}

const MegaMenu = React.forwardRef<HTMLUListElement, MegaMenuProps>(
  ({ items, className, ...props }, ref) => {
    const [openMenu, setOpenMenu] = React.useState<string | null>(null);
    const [isHover, setIsHover] = React.useState<number | null>(null);

    const handleHover = (menuLabel: string | null) => {
      setOpenMenu(menuLabel);
    };

    return (
      <ul
        ref={ref}
        className={`relative flex items-center space-x-0 ${className || ""}`}
        {...props}
      >
        {items.map((navItem) => (
          <li
            key={navItem.label}
            className="relative"
            onMouseEnter={() => handleHover(navItem.label)}
            onMouseLeave={() => handleHover(null)}
          >
            <button
              className="relative flex cursor-pointer items-center justify-center gap-1 py-1.5 px-4 text-sm text-white/50 transition-colors duration-300 hover:text-white group"
              onMouseEnter={() => setIsHover(navItem.id)}
              onMouseLeave={() => setIsHover(null)}
            >
              <span>{navItem.label}</span>
              {navItem.subMenus && (
                <ChevronDown
                  className={`h-4 w-4 transition-transform duration-300 group-hover:rotate-180 ${
                    openMenu === navItem.label ? "rotate-180" : ""
                  }`}
                />
              )}
              {(isHover === navItem.id || openMenu === navItem.label) && (
                <motion.div
                  layoutId="hover-bg"
                  className="absolute inset-0 size-full bg-white/10"
                  style={{ borderRadius: 99 }}
                />
              )}
            </button>

            {/* Pour les liens simples, pas de sous-menu */}
          </li>
        ))}
      </ul>
    );
  }
);

MegaMenu.displayName = "MegaMenu";

export default MegaMenu;


