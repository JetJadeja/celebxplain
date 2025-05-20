"use client";

import React, { useState, useEffect } from "react";
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
} from "lucide-react";

// Assuming ProcessSteps is now in a separate file and styled with Tailwind
import { ProcessSteps } from "@/components/process-steps";

// --- New Celebrity Card Component (Shadcn/Tailwind) ---
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
    <Card
      className={`w-[200px] text-center transition-all duration-200 ease-in-out cursor-pointer hover:shadow-lg ${
        isSelected ? "ring-2 ring-primary shadow-xl" : "shadow-md"
      } ${disabled ? "opacity-70 cursor-not-allowed" : ""}`}
      onClick={() => !disabled && onSelect(celebrity)}
    >
      <CardContent className="p-4 pt-6 flex flex-col items-center">
        <Image
          src={celebrity.image}
          alt={celebrity.name}
          width={80}
          height={80}
          className="rounded-full mb-3 border"
        />
        <h3
          className="font-semibold text-lg mb-2 truncate w-full"
          title={celebrity.name}
        >
          {celebrity.name}
        </h3>
        <Button
          onClick={(e: React.MouseEvent<HTMLButtonElement>) => {
            e.stopPropagation(); // Prevent card click when button is clicked
            if (!disabled) onSelect(celebrity);
          }}
          disabled={disabled}
          variant={isSelected ? "default" : "outline"}
          size="sm"
          className="w-full"
        >
          {isSelected ? "Selected" : "Select"}
        </Button>
      </CardContent>
    </Card>
  );
};

export default function DashboardPage() {
  // Renamed from Home to DashboardPage
  const [selectedCelebrity, setSelectedCelebrity] = useState<Celebrity | null>(
    null
  );
  const [topic, setTopic] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [celebrities, setCelebrities] = useState<Celebrity[]>([]);
  const [loadingCelebrities, setLoadingCelebrities] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  const { clearJob, createNewJob } = useJob();
  const router = useRouter();

  useEffect(() => {
    const loadCelebrities = async () => {
      try {
        setLoadingCelebrities(true);
        setLoadError(null);
        const data = await fetchPersonas();
        setCelebrities(data);
      } catch (err) {
        setLoadError(
          err instanceof Error ? err.message : "Failed to load celebrities"
        );
        console.error("Error loading celebrities:", err);
      } finally {
        setLoadingCelebrities(false);
      }
    };
    loadCelebrities();
  }, []);

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
      setIsSubmitting(false);
    }
  };

  const steps = [
    {
      title: "Select Celebrity & Topic",
      description: "Choose who explains and what they explain.",
      icon: <ListChecks size={24} />,
    },
    {
      title: "AI Generates Script",
      description: "Our AI crafts a personalized script in their style.",
      icon: <Wand2 size={24} />,
    },
    {
      title: "Watch Your Video",
      description: "Enjoy your unique, celebrity-narrated explanation!",
      icon: <Film size={24} />,
    },
  ];

  const canSubmit = selectedCelebrity && topic.trim() && !isSubmitting;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 text-slate-50 flex flex-col items-center justify-center p-4 sm:p-6 lg:p-8">
      <Card className="w-full max-w-4xl shadow-2xl bg-slate-800/70 backdrop-blur-md border-slate-700">
        <CardHeader className="text-center pb-4 pt-8">
          <div className="inline-flex items-center justify-center bg-primary/10 p-3 rounded-full mb-4 border border-primary/30">
            <Brain size={40} className="text-primary" />
          </div>
          <CardTitle className="text-3xl sm:text-4xl font-bold tracking-tight bg-gradient-to-r from-purple-400 via-pink-500 to-red-500 text-transparent bg-clip-text">
            Celebrity Explainer Generator Dashboard
          </CardTitle>
          <CardDescription className="text-base sm:text-lg text-slate-400 mt-2">
            Create new explanations or view your existing ones.
          </CardDescription>
        </CardHeader>

        <CardContent className="p-6 sm:p-8 space-y-8">
          {/* --- Process Steps Section --- */}
          <section aria-labelledby="process-steps-title">
            <h2
              id="process-steps-title"
              className="text-2xl font-semibold text-center mb-6 text-slate-200"
            >
              How It Works
            </h2>
            <ProcessSteps steps={steps} />
          </section>

          {/* --- Celebrity Selection Area --- */}
          <section aria-labelledby="celebrity-selection-title">
            <h2
              id="celebrity-selection-title"
              className="text-2xl font-semibold text-slate-200 mb-4"
            >
              1. Choose Your Celebrity
            </h2>
            {loadingCelebrities && (
              <div className="flex flex-col items-center justify-center text-slate-400 py-8">
                <Loader2 size={32} className="animate-spin mb-3" />
                <p>Loading celebrities...</p>
                <Progress value={50} className="w-1/2 mt-3 h-2 bg-slate-700" />
              </div>
            )}
            {!loadingCelebrities && celebrities.length > 0 && (
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
                {celebrities.map((celeb) => (
                  <CelebrityCard
                    key={celeb.id}
                    celebrity={celeb}
                    isSelected={selectedCelebrity?.id === celeb.id}
                    onSelect={setSelectedCelebrity}
                    disabled={isSubmitting}
                  />
                ))}
              </div>
            )}
            {!loadingCelebrities && celebrities.length === 0 && !loadError && (
              <Alert
                variant="default"
                className="bg-slate-700 border-slate-600"
              >
                <User size={20} className="text-slate-400" />
                <AlertTitle className="text-slate-300">
                  No Celebrities Found
                </AlertTitle>
                <AlertDescription className="text-slate-400">
                  We couldn't find any celebrities to choose from at the moment.
                </AlertDescription>
              </Alert>
            )}
          </section>

          {/* --- Topic Input Area --- */}
          <section aria-labelledby="topic-input-title">
            <h2
              id="topic-input-title"
              className="text-2xl font-semibold text-slate-200 mb-4"
            >
              2. Enter Your Topic
            </h2>
            <div className="relative">
              <Search
                size={20}
                className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500"
              />
              <Input
                type="text"
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                placeholder="e.g., Quantum Physics, How to Bake Sourdough, The History of Jazz..."
                disabled={isSubmitting}
                className="w-full text-lg p-4 pl-10 bg-slate-700 border-slate-600 placeholder:text-slate-500 focus:ring-primary focus:border-primary"
              />
            </div>
            {selectedCelebrity && (
              <p className="text-sm text-slate-400 mt-2 ml-1">
                Explaining "{topic || "..."}" as {selectedCelebrity.name}
              </p>
            )}
          </section>

          {/* --- Submission Area --- */}
          <section aria-labelledby="submission-title" className="pt-6">
            {loadError && (
              <Alert
                variant="destructive"
                className="mb-6 bg-red-900/30 border-red-700 text-red-300"
              >
                <AlertCircle className="h-4 w-4" />
                <AlertTitle>Error</AlertTitle>
                <AlertDescription>{loadError}</AlertDescription>
              </Alert>
            )}
            <Button
              onClick={handleGenerate}
              disabled={!canSubmit}
              className="w-full text-lg py-6 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 disabled:opacity-50 transition-all duration-300 ease-in-out transform hover:scale-105 flex items-center justify-center space-x-2"
            >
              {isSubmitting ? (
                <Loader2 size={24} className="animate-spin" />
              ) : (
                <CheckCircle size={24} />
              )}
              <span>
                {isSubmitting
                  ? "Generating Your Explanation..."
                  : "Generate Explanation Video"}
              </span>
            </Button>
          </section>
        </CardContent>
      </Card>

      <footer className="text-center py-8 text-slate-500 text-sm">
        <p>
          &copy; {new Date().getFullYear()} Celebrity Explainer. All rights
          reserved.
        </p>
        <p>Powered by AI magic.</p>
      </footer>
    </div>
  );
}
