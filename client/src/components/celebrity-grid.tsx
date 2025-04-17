"use client";

import React, { useState, useEffect } from "react";
import Image from "next/image";
import { Card, CardContent } from "@/components/ui/card";
import { fetchPersonas, type Celebrity } from "@/lib/api";

interface CelebrityGridProps {
  onSelect: (celebrity: Celebrity) => void;
  selectedId?: string;
}

export function CelebrityGrid({ onSelect, selectedId }: CelebrityGridProps) {
  const [celebrities, setCelebrities] = useState<Celebrity[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadCelebrities = async () => {
      try {
        setLoading(true);
        const data = await fetchPersonas();
        setCelebrities(data);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to load celebrities"
        );
        console.error("Error loading celebrities:", err);
      } finally {
        setLoading(false);
      }
    };

    loadCelebrities();
  }, []);

  if (loading) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        {[...Array(6)].map((_, index) => (
          <Card key={index} className="animate-pulse">
            <CardContent className="p-4 flex flex-col items-center">
              <div className="w-24 h-24 rounded-full bg-primary/20 mb-2" />
              <div className="h-4 w-24 bg-primary/20 rounded" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 border border-destructive/20 bg-destructive/10 rounded-md text-destructive">
        <p>Failed to load celebrities: {error}</p>
        <p className="text-sm mt-2">Please try refreshing the page.</p>
      </div>
    );
  }

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
