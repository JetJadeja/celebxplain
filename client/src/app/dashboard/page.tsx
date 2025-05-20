"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useJob } from "@/lib/job-context";
import { fetchPersonas, type Celebrity } from "@/lib/api";
import Image from "next/image";

// Shadcn UI & Lucide Icons
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
  CardFooter,
} from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import {
  Loader2,
  AlertCircle,
  User,
  Brain,
  Film,
  Search,
  ListChecks,
  CheckCircle,
  Wand2,
  Sparkles,
  ChevronRight,
  Lightbulb,
  Users,
  MicVocal,
  MessageSquareText,
  Info,
  Star,
} from "lucide-react";

// Removed ProcessSteps import, will integrate its content differently or simplify

// --- Celebrity Card Component ---
// Attempting a new style for the celebrity cards for a fresher look.
interface CelebrityCardProps {
  celebrity: Celebrity;
  isSelected: boolean;
  onSelect: (celebrity: Celebrity) => void;
  disabled: boolean;
}

const CelebrityCard: React.FC<CelebrityCardProps> = ({
  celebrity,
  isSelected,
  onSelect,
  disabled,
}) => {
  return (
    <div
      onClick={() => !disabled && onSelect(celebrity)}
      className={`
        group relative rounded-xl border p-4 transition-all duration-300 ease-in-out cursor-pointer 
        flex flex-col items-center justify-start text-center
        ${
          disabled
            ? "opacity-50 cursor-not-allowed grayscale"
            : "hover:shadow-2xl hover:border-primary/80"
        }
        ${
          isSelected
            ? "bg-primary/10 border-primary ring-2 ring-primary shadow-2xl"
            : "bg-slate-800/70 border-slate-700/80 hover:bg-slate-700/90"
        }
      `}
    >
      <Image
        src={celebrity.image}
        alt={celebrity.name}
        width={88} // Larger image
        height={88}
        className={`rounded-full mb-4 border-4 transition-all duration-300 
          ${
            isSelected
              ? "border-primary/70"
              : "border-slate-600 group-hover:border-primary/50"
          }
        `}
      />
      <h3
        className="font-medium text-lg leading-tight text-slate-50 mb-1 truncate w-full"
        title={celebrity.name}
      >
        {celebrity.name}
      </h3>
      <p className="text-xs text-slate-400 group-hover:text-slate-300 mb-4 h-8">
        {" "}
        {/* Placeholder for potential brief description if added later */}
        {/* Example: AI Persona */}
      </p>
      <Button
        variant={isSelected ? "default" : "outline"}
        size="sm"
        className={`w-full mt-auto text-sm transition-all duration-200 
            ${
              isSelected
                ? "bg-primary hover:bg-primary/90"
                : "border-slate-600 hover:border-primary hover:text-primary bg-slate-700/50 hover:bg-slate-700"
            }
            ${disabled ? "opacity-70" : ""}
          `}
        disabled={disabled}
      >
        {isSelected ? (
          <CheckCircle size={16} className="mr-2" />
        ) : (
          <Star size={16} className="mr-2" />
        )}
        {isSelected ? "Selected" : "Choose"}
      </Button>
    </div>
  );
};

export default function DashboardPage() {
  const [selectedCelebrity, setSelectedCelebrity] = useState<Celebrity | null>(
    null
  );
  const [topic, setTopic] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [celebrities, setCelebrities] = useState<Celebrity[]>([]);
  const [loadingCelebrities, setLoadingCelebrities] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");

  const { clearJob, createNewJob } = useJob();
  const router = useRouter();

  useEffect(() => {
    const loadCelebrities = async () => {
      setLoadingCelebrities(true);
      setLoadError(null);
      try {
        const data = await fetchPersonas();
        setCelebrities(data);
      } catch (err) {
        setLoadError(
          err instanceof Error ? err.message : "Failed to load personas"
        );
        console.error("Error loading personas:", err);
      } finally {
        setLoadingCelebrities(false);
      }
    };
    loadCelebrities();
  }, []);

  const filteredCelebrities = celebrities.filter((celeb) =>
    celeb.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleGenerate = async () => {
    if (!selectedCelebrity || !topic.trim() || isSubmitting) return;
    setIsSubmitting(true);
    setLoadError(null);
    try {
      clearJob();
      const newJob = await createNewJob(topic.trim(), selectedCelebrity.id);
      router.push(`/results/${newJob.job_id}`);
    } catch (error) {
      console.error("Error creating job:", error);
      setLoadError("Failed to start explanation generation. Please try again.");
    } finally {
      setIsSubmitting(false); // Ensure this is always reset
    }
  };

  const canSubmit = selectedCelebrity && topic.trim() && !isSubmitting;

  // Simplified steps directly integrated or implied by the flow
  // const steps = [...];

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col items-center justify-center p-4 sm:p-8">
      <div className="w-full max-w-3xl mx-auto">
        {/* Header */}
        <header className="mb-10 text-center">
          <div className="inline-flex items-center justify-center bg-purple-600/20 p-3.5 rounded-full mb-5 shadow-lg border-2 border-purple-500/50">
            <Brain size={36} className="text-purple-300" />
          </div>
          <h1 className="text-4xl sm:text-5xl font-bold tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-purple-400 via-pink-400 to-orange-400 pb-2">
            AI Oracle Studio
          </h1>
          <p className="text-lg text-slate-400 max-w-xl mx-auto">
            Craft engaging video explanations with your favorite AI personas.
            It's simple: Pick a persona, enter your topic, and let the AI work
            its magic.
          </p>
        </header>

        {/* Main Creation Workflow in a single Card */}
        <Card className="w-full shadow-2xl bg-slate-900/80 border-slate-700/60 backdrop-blur-lg">
          <CardContent className="p-6 sm:p-8 space-y-8">
            {/* Step 1: Choose Persona */}
            <section aria-labelledby="persona-selection-title">
              <div className="flex flex-col md:flex-row justify-between md:items-center mb-5">
                <h2
                  id="persona-selection-title"
                  className="text-2xl font-semibold text-slate-100 flex items-center mb-3 md:mb-0"
                >
                  <MicVocal size={24} className="mr-3 text-purple-400" />
                  Choose Your Persona
                </h2>
                <div className="relative w-full md:w-auto md:min-w-[250px]">
                  <Search
                    size={18}
                    className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500 pointer-events-none"
                  />
                  <Input
                    type="text"
                    placeholder="Search personas..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full pl-10 pr-4 py-2.5 bg-slate-800 border-slate-700 focus:ring-purple-500 focus:border-purple-500 rounded-lg text-sm"
                    disabled={loadingCelebrities || isSubmitting}
                  />
                </div>
              </div>

              {loadingCelebrities && (
                <div className="flex flex-col items-center justify-center text-slate-400 py-10 text-center">
                  <Loader2
                    size={36}
                    className="animate-spin mb-4 text-purple-400"
                  />
                  <p className="text-base font-medium text-slate-300">
                    Loading Personas...
                  </p>
                  <Progress
                    value={66}
                    className="w-1/2 mt-4 h-1.5 bg-slate-700 rounded-full"
                  />
                </div>
              )}

              {!loadingCelebrities &&
                celebrities.length > 0 &&
                (filteredCelebrities.length > 0 ? (
                  <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
                    {filteredCelebrities.map((celeb) => (
                      <CelebrityCard
                        key={celeb.id}
                        celebrity={celeb}
                        isSelected={selectedCelebrity?.id === celeb.id}
                        onSelect={setSelectedCelebrity}
                        disabled={isSubmitting}
                      />
                    ))}
                  </div>
                ) : (
                  <Alert
                    variant="default"
                    className="bg-slate-800/70 border-slate-700 text-center py-6"
                  >
                    <Search
                      size={22}
                      className="mx-auto mb-2.5 text-slate-500"
                    />
                    <AlertTitle className="text-lg font-medium text-slate-300">
                      No Matching Personas
                    </AlertTitle>
                    <AlertDescription className="text-slate-400 text-sm">
                      No personas found for "{searchTerm}". Try a different
                      search.
                    </AlertDescription>
                  </Alert>
                ))}

              {!loadingCelebrities &&
                celebrities.length === 0 &&
                !loadError && (
                  <Alert
                    variant="default"
                    className="bg-slate-800/70 border-slate-700 text-center py-6"
                  >
                    <User size={22} className="mx-auto mb-2.5 text-slate-500" />
                    <AlertTitle className="text-lg font-medium text-slate-300">
                      No Personas Available
                    </AlertTitle>
                    <AlertDescription className="text-slate-400 text-sm">
                      Check back later or ensure personas are loaded correctly.
                    </AlertDescription>
                  </Alert>
                )}
            </section>

            {/* Step 2: Enter Topic */}
            <section aria-labelledby="topic-input-title">
              <h2
                id="topic-input-title"
                className="text-2xl font-semibold text-slate-100 mb-4 flex items-center"
              >
                <Lightbulb size={24} className="mr-3 text-purple-400" />
                Enter Your Topic
              </h2>
              <div className="relative">
                <Input
                  type="text"
                  value={topic}
                  onChange={(e) => setTopic(e.target.value)}
                  placeholder="e.g., How do black holes work? The story of the internet..."
                  disabled={isSubmitting || !selectedCelebrity}
                  className="w-full text-base p-3.5 pl-4 bg-slate-800 border-slate-700 placeholder:text-slate-500 focus:ring-purple-500 focus:border-purple-500 rounded-lg disabled:opacity-60 disabled:cursor-not-allowed"
                  aria-describedby="topic-helper-text"
                />
              </div>
              {selectedCelebrity && (
                <p
                  id="topic-helper-text"
                  className="text-xs text-slate-400 mt-2 ml-1"
                >
                  {topic.trim() === ""
                    ? `What should ${selectedCelebrity.name} explain?`
                    : `Explaining "${topic}" as ${selectedCelebrity.name}.`}
                </p>
              )}
              {!selectedCelebrity && (
                <p
                  id="topic-helper-text"
                  className="text-xs text-slate-500 mt-2 ml-1"
                >
                  Select a persona above to enable topic input.
                </p>
              )}
            </section>

            {/* Error Display Area (moved above button for clarity) */}
            {loadError && (
              <Alert
                variant="destructive"
                className="mb-0 bg-red-700/20 border-red-600/50 text-red-300"
              >
                <AlertCircle className="h-5 w-5 text-red-400" />
                <AlertTitle>Error</AlertTitle>
                <AlertDescription>{loadError}</AlertDescription>
              </Alert>
            )}
          </CardContent>

          {/* Footer of the card for the main action */}
          <CardFooter className="p-6 sm:p-8 border-t border-slate-700/60 mt-4">
            <Button
              onClick={handleGenerate}
              disabled={!canSubmit}
              size="lg"
              className="w-full text-base py-6 bg-gradient-to-r from-purple-600 via-pink-500 to-orange-500 hover:from-purple-700 hover:via-pink-600 hover:to-orange-600 
                           disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 ease-in-out 
                           transform hover:scale-[1.01] group rounded-lg shadow-lg hover:shadow-purple-500/30 focus:ring-2 focus:ring-offset-2 focus:ring-offset-slate-900 focus:ring-pink-500"
            >
              {isSubmitting ? (
                <Loader2 size={22} className="animate-spin mr-2.5" />
              ) : (
                <Sparkles
                  size={20}
                  className="mr-2.5 transition-transform duration-300 group-hover:scale-110"
                />
              )}
              <span>
                {isSubmitting
                  ? "Generating AI Magic..."
                  : "Create Explanation Video"}
              </span>
              {!isSubmitting && (
                <ChevronRight
                  size={22}
                  className="ml-1.5 opacity-70 transition-all duration-300 group-hover:translate-x-1 group-hover:opacity-100"
                />
              )}
            </Button>
          </CardFooter>
        </Card>

        {isSubmitting && (
          <p className="text-center text-slate-500 mt-6 text-sm">
            Oracle is thinking... This may take a few moments.
          </p>
        )}

        {/* Simplified Footer */}
        <footer className="text-center pt-12 pb-6 text-slate-600 text-xs">
          <p>
            &copy; {new Date().getFullYear()} Oracle AI. All Rights Reserved.
          </p>
        </footer>
      </div>
    </div>
  );
}
