"use client";

import React, { useLayoutEffect, useRef, useCallback } from "react";
import type { ReactNode } from "react";
import Lenis from "lenis";

export interface ScrollStackItemProps {
  children: ReactNode;
  className?: string;
}

export const ScrollStackItem: React.FC<ScrollStackItemProps> = ({ children, className = "" }) => (
  <div className={`scroll-stack-card ${className}`.trim()}>{children}</div>
);

interface ScrollStackProps {
  children: ReactNode;
  className?: string;
}

const ScrollStack: React.FC<ScrollStackProps> = ({ children, className = "" }) => {
  const scrollerRef = useRef<HTMLDivElement>(null);
  const animationFrameRef = useRef<number | null>(null);
  const lenisRef = useRef<Lenis | null>(null);
  const cardsRef = useRef<HTMLElement[]>([]);
  const lastTransformsRef = useRef(new Map<number, any>());

  const ITEM_DISTANCE = 80;
  const ITEM_SCALE = 0.03;
  const ITEM_STACK_DISTANCE = 30;
  const STACK_POSITION = "20%";
  const SCALE_END_POSITION = "10%";
  const BASE_SCALE = 0.85;
  const BLUR_AMOUNT = 2;

  const calculateProgress = useCallback((scrollTop: number, start: number, end: number) => {
    if (scrollTop < start) return 0;
    if (scrollTop > end) return 1;
    return (scrollTop - start) / (end - start);
  }, []);

  const parsePercentage = useCallback((value: string, containerHeight: number) => {
    if (value.includes("%")) return (parseFloat(value) / 100) * containerHeight;
    return parseFloat(value);
  }, []);

  const updateCardTransforms = useCallback(() => {
    if (!cardsRef.current.length) return;
    const scroller = scrollerRef.current;
    if (!scroller) return;

    const scrollTop = scroller.scrollTop;
    const containerHeight = scroller.clientHeight;
    const stackPositionPx = parsePercentage(STACK_POSITION, containerHeight);
    const scaleEndPositionPx = parsePercentage(SCALE_END_POSITION, containerHeight);

    const endElement = scroller.querySelector(".scroll-stack-end") as HTMLElement;
    const endElementTop = endElement ? endElement.offsetTop : 0;

    let topCardIndex = 0;
    cardsRef.current.forEach((card, i) => {
      const cardTop = card.offsetTop;
      const triggerStart = cardTop - stackPositionPx - ITEM_STACK_DISTANCE * i;
      if (scrollTop >= triggerStart) topCardIndex = i;
    });

    cardsRef.current.forEach((card, i) => {
      if (!card) return;

      const cardTop = card.offsetTop;
      const triggerStart = cardTop - stackPositionPx - ITEM_STACK_DISTANCE * i;
      const triggerEnd = cardTop - scaleEndPositionPx;
      const pinStart = cardTop - stackPositionPx - ITEM_STACK_DISTANCE * i;
      const pinEnd = endElementTop - containerHeight / 2;

      const scaleProgress = calculateProgress(scrollTop, triggerStart, triggerEnd);
      const targetScale = BASE_SCALE + i * ITEM_SCALE;
      const scale = 1 - scaleProgress * (1 - targetScale);

      let blur = 0;
      if (i < topCardIndex) {
        blur = Math.max(0, (topCardIndex - i) * BLUR_AMOUNT);
      }

      let translateY = 0;
      const isPinned = scrollTop >= pinStart && scrollTop <= pinEnd;
      if (isPinned) {
        translateY = scrollTop - cardTop + stackPositionPx + ITEM_STACK_DISTANCE * i;
      } else if (scrollTop > pinEnd) {
        translateY = pinEnd - cardTop + stackPositionPx + ITEM_STACK_DISTANCE * i;
      }

      const newTransform = {
        translateY: Math.round(translateY * 100) / 100,
        scale: Math.round(scale * 1000) / 1000,
        blur: Math.round(blur * 100) / 100,
      };

      const lastTransform = lastTransformsRef.current.get(i);
      const hasChanged =
        !lastTransform ||
        Math.abs(lastTransform.translateY - newTransform.translateY) > 0.1 ||
        Math.abs(lastTransform.scale - newTransform.scale) > 0.001 ||
        Math.abs(lastTransform.blur - newTransform.blur) > 0.1;

      if (hasChanged) {
        card.style.transform = `translate3d(0, ${newTransform.translateY}px, 0) scale(${newTransform.scale})`;
        card.style.filter = newTransform.blur > 0 ? `blur(${newTransform.blur}px)` : "";
        card.style.opacity = newTransform.blur > 3 ? "0.6" : "1";
        lastTransformsRef.current.set(i, newTransform);
      }
    });
  }, [calculateProgress, parsePercentage]);

  const handleScroll = useCallback(() => {
    updateCardTransforms();
  }, [updateCardTransforms]);

  useLayoutEffect(() => {
    const scroller = scrollerRef.current;
    if (!scroller) return;

    const cards = Array.from(scroller.querySelectorAll(".scroll-stack-card")) as HTMLElement[];
    cardsRef.current = cards;

    cards.forEach((card, i) => {
      if (i < cards.length - 1) card.style.marginBottom = `${ITEM_DISTANCE}px`;
      card.style.willChange = "transform, filter, opacity";
      card.style.transformOrigin = "top center";
      card.style.backfaceVisibility = "hidden";
      card.style.transform = "translateZ(0)";
    });

    const lenis = new Lenis({
      wrapper: scroller,
      content: scroller.querySelector(".scroll-stack-inner") as HTMLElement,
      duration: 1.2,
      easing: (t: number) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
      smoothWheel: true,
      touchMultiplier: 2,
      wheelMultiplier: 1,
      lerp: 0.1,
    });

    lenis.on("scroll", handleScroll);

    const raf = (time: number) => {
      lenis.raf(time);
      animationFrameRef.current = requestAnimationFrame(raf);
    };
    animationFrameRef.current = requestAnimationFrame(raf);
    lenisRef.current = lenis;

    updateCardTransforms();

    return () => {
      if (animationFrameRef.current) cancelAnimationFrame(animationFrameRef.current);
      if (lenisRef.current) lenisRef.current.destroy();
      cardsRef.current = [];
      lastTransformsRef.current.clear();
    };
  }, [handleScroll, updateCardTransforms]);

  return (
    <div className={`scroll-stack-scroller ${className}`.trim()} ref={scrollerRef}>
      <div className="scroll-stack-inner">
        {children}
        <div className="scroll-stack-end" />
      </div>
    </div>
  );
};

export default ScrollStack;
