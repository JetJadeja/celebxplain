"use client";

import React from "react";
import useEmblaCarousel from "embla-carousel-react";
// import Autoplay from "embla-carousel-autoplay"; // Remove Autoplay
import AutoScroll from "embla-carousel-auto-scroll"; // Add AutoScroll
import Image from "next/image";

const PLACEHOLDER_IMAGES = [
  {
    src: "https://picsum.photos/seed/carousel1/600/400",
    alt: "Placeholder Image 1",
    title: "Inspirational Ideas",
  },
  {
    src: "https://picsum.photos/seed/carousel2/600/400",
    alt: "Placeholder Image 2",
    title: "Creative Concepts",
  },
  {
    src: "https://picsum.photos/seed/carousel3/600/400",
    alt: "Placeholder Image 3",
    title: "Educational Insights",
  },
  {
    src: "https://picsum.photos/seed/carousel4/600/400",
    alt: "Placeholder Image 4",
    title: "Personal Messages",
  },
  {
    src: "https://picsum.photos/seed/carousel5/600/400",
    alt: "Placeholder Image 5",
    title: "Expert Explanations",
  },
  {
    src: "https://picsum.photos/seed/carousel6/600/400",
    alt: "Placeholder Image 6",
    title: "Fun Facts",
  },
  {
    src: "https://picsum.photos/seed/carousel7/600/400",
    alt: "Placeholder Image 7",
    title: "Quick Tutorials",
  },
  {
    src: "https://picsum.photos/seed/carousel8/600/400",
    alt: "Placeholder Image 8",
    title: "Daily Wisdom",
  },
];

export const PhotoCarousel = () => {
  const [emblaRef] = useEmblaCarousel(
    {
      loop: true,
      align: "start",
      containScroll: "trimSnaps",
    },
    [
      // Autoplay({
      //   delay: 3000,
      //   stopOnInteraction: false,
      //   stopOnMouseEnter: true,
      // }),
      AutoScroll({
        speed: 1, // Adjust speed as needed, 1 is a moderate default
        stopOnInteraction: true, // Default, but good to be explicit
        stopOnMouseEnter: false, // Changed to false
      }),
    ]
  );

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
