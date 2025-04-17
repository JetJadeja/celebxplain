import React from "react";

interface Step {
  title: string;
  description: string;
  icon: React.ReactNode;
}

interface ProcessStepsProps {
  steps: Step[];
}

export function ProcessSteps({ steps }: ProcessStepsProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-8 w-full max-w-4xl mx-auto">
      {steps.map((step, index) => (
        <div
          key={index}
          className="flex flex-col items-center text-center space-y-3"
        >
          <div className="flex items-center justify-center w-16 h-16 rounded-full bg-gradient-to-r from-blue-600 to-teal-500 text-white text-2xl">
            {step.icon}
          </div>
          <div className="relative">
            <h3 className="text-lg font-medium">{step.title}</h3>
            {index < steps.length - 1 && (
              <div className="hidden md:block absolute top-1/2 left-full w-full h-0.5 bg-gradient-to-r from-blue-600 to-teal-500" />
            )}
          </div>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            {step.description}
          </p>
        </div>
      ))}
    </div>
  );
}
