import React from "react";
import Image from "next/image";
import { Card, CardContent } from "@/components/ui/card";

type Celebrity = {
  id: string;
  name: string;
  image: string;
};

// Sample celebrity data - in a real app, this would come from an API
const defaultCelebrities: Celebrity[] = [
  { id: "1", name: "Morgan Freeman", image: "/placeholder-avatar.svg" },
  { id: "2", name: "Taylor Swift", image: "/placeholder-avatar.svg" },
  { id: "3", name: "Neil deGrasse Tyson", image: "/placeholder-avatar.svg" },
  { id: "4", name: "Oprah Winfrey", image: "/placeholder-avatar.svg" },
  { id: "5", name: "Elon Musk", image: "/placeholder-avatar.svg" },
  { id: "6", name: "Beyoncé", image: "/placeholder-avatar.svg" },
];

interface CelebrityGridProps {
  celebrities?: Celebrity[];
  onSelect: (celebrity: Celebrity) => void;
  selectedId?: string;
}

export function CelebrityGrid({
  celebrities = defaultCelebrities,
  onSelect,
  selectedId,
}: CelebrityGridProps) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
      {celebrities.map((celebrity) => (
        <Card
          key={celebrity.id}
          className={`cursor-pointer transition-all hover:scale-105 ${
            selectedId === celebrity.id
              ? "ring-2 ring-primary ring-offset-2"
              : ""
          }`}
          onClick={() => onSelect(celebrity)}
        >
          <CardContent className="p-4 flex flex-col items-center">
            <div className="relative w-24 h-24 rounded-full overflow-hidden mb-2">
              <Image
                src={celebrity.image}
                alt={celebrity.name}
                fill
                className="object-cover"
              />
            </div>
            <h3 className="font-medium text-center">{celebrity.name}</h3>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
