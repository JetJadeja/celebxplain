"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useJob } from "@/lib/job-context";
import { fetchPersonas, type Celebrity } from "@/lib/api";
import {
  Window,
  WindowHeader,
  WindowContent,
  Button as R95Button,
  TextInput,
  GroupBox,
  Frame,
  ProgressBar,
} from "react95";
import Image from "next/image";

// --- Celebrity Card Component ---
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
    <GroupBox
      label={celebrity.name}
      style={{
        width: "200px",
        textAlign: "center",
        margin: "0.5rem",
        padding: "0.5rem",
        paddingTop: "1.5rem",
        boxShadow: isSelected
          ? "inset 2px 2px 4px rgba(0,0,0,0.3)"
          : "2px 2px 4px rgba(0,0,0,0.2)",
        border: isSelected ? "1px solid gray" : "1px solid silver",
      }}
    >
      <Image
        src={celebrity.image}
        alt={celebrity.name}
        width={80}
        height={80}
        style={{
          borderRadius: "50%",
          marginBottom: "0.75rem",
          border: "1px solid silver",
          display: "inline-block",
        }}
      />
      <R95Button
        onClick={() => onSelect(celebrity)}
        disabled={disabled}
        fullWidth
      >
        Select
      </R95Button>
    </GroupBox>
  );
};

// Process Steps Component using Frame
const R95ProcessSteps = ({
  steps,
}: {
  steps: { title: string; description: string; icon: React.ReactNode }[];
}) => {
  return (
    <div
      style={{
        display: "flex",
        justifyContent: "space-around",
        gap: "0.75rem",
        padding: "0.5rem 0.25rem",
      }}
    >
      {steps.map((step, index) => (
        <Frame
          key={index}
          variant="well"
          style={{
            padding: "0.75rem 0.5rem",
            textAlign: "center",
            flex: 1,
          }}
        >
          <div
            style={{
              fontSize: "1.5rem",
              marginBottom: "0.5rem",
              fontFamily: "monospace",
            }}
          >
            {step.icon}
          </div>
          <h3
            style={{
              fontWeight: "bold",
              fontSize: "0.9rem",
              marginBottom: "0.3rem",
            }}
          >
            {step.title}
          </h3>
          <p style={{ fontSize: "0.8rem" }}>{step.description}</p>
        </Frame>
      ))}
    </div>
  );
};

export default function Home() {
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

  // Fetch celebrities on mount
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
    if (!selectedCelebrity || !topic || isSubmitting) return;
    setIsSubmitting(true);
    setLoadError(null);
    try {
      clearJob();
      const newJob = await createNewJob(topic, selectedCelebrity.id);
      router.push(`/results/${newJob.job_id}`);
    } catch (error) {
      console.error("Error creating job:", error);
      setLoadError("Failed to start explanation generation. Please try again.");
      setIsSubmitting(false);
    }
  };

  // Define steps with placeholder icons (replace with actual icons if available)
  const steps = [
    {
      title: "Select & Topic",
      description: "Choose who explains",
      icon: "[1]",
    },
    {
      title: "AI Generates",
      description: "Personalized script",
      icon: "[2]",
    },
    {
      title: "Watch Video",
      description: "Enjoy your explanation",
      icon: "[3]",
    },
  ];

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "teal",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "2rem",
      }}
    >
      <Window
        style={{
          width: "95%",
          height: "90vh",
          maxWidth: "1000px",
          maxHeight: "800px",
          margin: "auto",
        }}
      >
        <WindowHeader>Celebrity Explainer Generator</WindowHeader>
        <WindowContent
          style={{
            display: "flex",
            flexDirection: "column",
            height: "calc(100% - 28px)",
            padding: "0.25rem",
          }}
        >
          {/* --- Header Text --- */}
          <div
            style={{
              maxWidth: "960px",
              margin: "0 auto",
              display: "flex",
              flexDirection: "column",
              flexGrow: 1,
            }}
          >
            <div
              style={{ textAlign: "center", padding: "0.25rem 0 0.75rem 0" }}
            >
              <h1
                style={{
                  fontSize: "1.5rem",
                  fontWeight: "bold",
                  marginBottom: "0.3rem",
                }}
              >
                Celebrity Explainer Generator
              </h1>
              <p>Learn anything, explained by your favorite celebrities</p>
            </div>

            {/* --- Celebrity Selection Area --- */}
            <GroupBox
              label="1. Choose a Celebrity"
              style={{ marginBottom: "0.5rem" }}
            >
              {(() => {
                // Use standard if/else if/else for clarity
                if (loadingCelebrities) {
                  return (
                    <Frame
                      variant="well"
                      style={{
                        padding: "1rem",
                        textAlign: "center",
                        height: "200px",
                        display: "flex",
                        flexDirection: "column",
                        justifyContent: "center",
                        alignItems: "center",
                      }}
                    >
                      <p style={{ marginBottom: "1rem" }}>
                        Loading celebrities...
                      </p>
                      <ProgressBar style={{ width: "90%" }} />
                    </Frame>
                  );
                }

                if (loadError && !celebrities.length) {
                  return (
                    <Frame
                      variant="well"
                      style={{
                        padding: "1rem",
                        color: "red",
                        textAlign: "center",
                        height: "200px",
                        display: "flex",
                        justifyContent: "center",
                        alignItems: "center",
                      }}
                    >
                      <p>Error loading celebrities: {loadError}</p>
                    </Frame>
                  );
                }

                // Default case: display celebrities
                return (
                  <div
                    style={{
                      height: "260px",
                      overflowY: "auto",
                      padding: "0.25rem",
                      display: "flex",
                      flexWrap: "wrap",
                      justifyContent: "flex-start",
                      alignItems: "flex-start",
                      background: "silver",
                    }}
                  >
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
                );
              })()}
            </GroupBox>

            {/* --- Topic Input Area --- */}
            <GroupBox
              label="2. What would you like explained?"
              style={{ marginBottom: "0.5rem" }}
            >
              <TextInput
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                placeholder="Enter any topic or question..."
                style={{ marginBottom: "0.5rem" }}
                disabled={isSubmitting}
                fullWidth
              />
              <R95Button
                onClick={handleGenerate}
                disabled={!selectedCelebrity || !topic || isSubmitting}
                fullWidth
                style={{ height: "36px" }}
              >
                {isSubmitting ? "Creating..." : "Generate Explanation"}
              </R95Button>

              <div style={{ marginTop: "0.5rem" }}>
                {!isSubmitting && !selectedCelebrity && !topic && (
                  <Frame variant="status" style={{ padding: "0.25rem 0.5rem" }}>
                    <p style={{ fontSize: "0.875rem" }}>
                      Select a celebrity and enter a topic above.
                    </p>
                  </Frame>
                )}
                {!isSubmitting && selectedCelebrity && topic && (
                  <Frame variant="well" style={{ padding: "0.35rem 0.5rem" }}>
                    <p style={{ fontSize: "0.875rem" }}>
                      Ready: <strong>{selectedCelebrity.name}</strong> will
                      explain <strong>{topic}</strong>
                    </p>
                  </Frame>
                )}
                {isSubmitting && (
                  <Frame
                    variant="status"
                    style={{
                      padding: "0.35rem 0.5rem",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                    }}
                  >
                    <p style={{ fontSize: "0.875rem", marginRight: "1rem" }}>
                      Generating explanation...
                    </p>
                    <ProgressBar style={{ width: "150px" }} />
                  </Frame>
                )}
                {loadError && !loadingCelebrities && (
                  <Frame
                    variant="well"
                    style={{
                      padding: "0.35rem 0.5rem",
                      color: "red",
                      marginTop: "0.5rem",
                    }}
                  >
                    <p>Error: {loadError}</p>
                  </Frame>
                )}
              </div>
            </GroupBox>

            {/* --- Process Visualization Area --- */}
            <GroupBox label="How It Works" style={{ flexShrink: 0 }}>
              <R95ProcessSteps steps={steps} />
            </GroupBox>
          </div>

          {/* --- Footer (stays outside the max-width container) --- */}
          <Frame
            variant="status"
            style={{
              marginTop: "auto",
              padding: "0.15rem 0.5rem",
              textAlign: "center",
              flexShrink: 0,
            }}
          >
            © {new Date().getFullYear()} Celebrity Explainer Generator
          </Frame>
        </WindowContent>
      </Window>
    </div>
  );
}
