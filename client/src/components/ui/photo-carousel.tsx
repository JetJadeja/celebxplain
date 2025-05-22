"use client";

import React from "react";
import useEmblaCarousel from "embla-carousel-react";
import { type EmblaOptionsType } from "embla-carousel";
import AutoScroll from "embla-carousel-auto-scroll";
import Image from "next/image";

const PLACEHOLDER_IMAGES = [
  {
    src: "https://edm.com/.image/ar_16:9%2Cc_fill%2Ccs_srgb%2Cg_xy_center%2Cq_auto:good%2Cw_768%2Cx_1200%2Cy_491/MTg2MDAwODk4ODUyMzk4MjA5/shaquille-oneal-dj-diesel-full-send-podcast-nelk-boys.png",
    alt: "Shaquille O'Neal DJ Diesel",
    title: "Mathematics",
  },
  {
    src: "https://cloudfront-us-east-1.images.arcpublishing.com/dmn/UXWAHKCZEBGCBOFJBW5AC4V3NA.png",
    alt: "Joe Rogan teaches physics",
    title: "History",
  },
  {
    src: "https://i.ytimg.com/vi/DhU6c6NIu1c/maxresdefault.jpg",
    alt: "Ice Spice teaches engineering",
    title: "Engineering",
  },
  {
    src: "https://mediaproxy.salon.com/width/1200/https://media2.salon.com/2014/01/wolf_wall_street2.jpg",
    alt: "Wolf of Wall Street",
    title: "Business",
  },
  {
    src: "https://media.cnn.com/api/v1/images/stellar/prod/221025160423-taylor-swift-jimmy-fallon.jpg?c=original",
    alt: "Taylor Swift Jimmy Fallon",
    title: "Negotiation",
  },
  {
    src: "https://images.cdn.prd.api.discomax.com/2023/02/17/ffd87025-dabb-389f-999c-457780b2b4ee.jpeg?f=jpg&q=75&w=1280",
    alt: "Donald Trump",
    title: "Software",
  },
];

export const PhotoCarousel = () => {
  const emblaOptions: EmblaOptionsType = {
    loop: true,
    align: "start",
    containScroll: "trimSnaps",
    watchDrag: false, // Disable manual dragging using watchDrag
  };

  const [emblaRef] = useEmblaCarousel(emblaOptions, [
    AutoScroll({
      speed: 1,
      stopOnInteraction: false, // Keep this false as well
      stopOnMouseEnter: false,
    }),
  ]);

  return (
    <section className="pb-12 md:pb-16">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="overflow-hidden" ref={emblaRef}>
          <div className="flex -ml-4">
            {[...PLACEHOLDER_IMAGES, ...PLACEHOLDER_IMAGES].map(
              (img, index) => (
                <div
                  className="flex-[0_0_80%] sm:flex-[0_0_40%] md:flex-[0_0_28%] lg:flex-[0_0_20%] pl-4"
                  key={index}
                >
                  <div className="relative aspect-[4/3] rounded-lg overflow-hidden group shadow-lg transition-all duration-300 hover:shadow-purple-500/30">
                    <Image
                      src={img.src}
                      alt={img.alt}
                      fill
                      sizes="(max-width: 640px) 80vw, (max-width: 768px) 40vw, (max-width: 1024px) 28vw, 20vw"
                      className="object-cover transition-transform duration-500 ease-in-out group-hover:scale-105"
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/30 to-transparent opacity-100 group-hover:opacity-100 transition-opacity duration-300"></div>
                    <div className="absolute bottom-0 left-0 p-3 sm:p-4 w-full">
                      <h3 className="text-sm sm:text-base font-semibold text-white truncate group-hover:text-purple-300 transition-colors">
                        {img.title}
                      </h3>
                    </div>
                    <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                      <div className="bg-white/30 backdrop-blur-sm rounded-full p-3 cursor-pointer">
                        <svg
                          xmlns="http://www.w3.org/2000/svg"
                          width="24"
                          height="24"
                          viewBox="0 0 24 24"
                          fill="white"
                        >
                          <path d="M8 5v14l11-7z" />
                        </svg>
                      </div>
                    </div>
                  </div>
                </div>
              )
            )}
          </div>
        </div>
      </div>
    </section>
  );
};

export default PhotoCarousel;
