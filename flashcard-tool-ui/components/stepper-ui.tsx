import { cn } from "@/lib/utils";

interface Step {
  number: number;
  label: string;
}

interface StepperUIProps {
  steps: Step[];
  currentStep: number;
}

export default function StepperUI({ steps, currentStep }: StepperUIProps) {
  return (
    <div className="w-full py-4">
      <div className="relative flex flex-col space-y-8">
        {/* Vertical connecting line */}
        <div className="absolute top-10 bottom-6 left-[1.35rem] w-1 bg-gray-200 z-0" />

        {steps.map((step, index) => (
          <div key={step.number} className="flex items-start z-10 relative">
            {/* Step circle */}
            <div
              className={cn(
                "w-12 h-12 rounded-full flex items-center justify-center font-medium text-xl border-4 z-10",
                currentStep === step.number
                  ? "bg-[#2B60D5] text-white border-[#214DCE]"
                  : currentStep > step.number
                    ? "bg-[#2B60D5] text-white border-[#214DCE]"
                    : "bg-white border-gray-300 text-black",
              )}
            >
              {step.number}
            </div>

            {/* Step content */}
            <div className="ml-3 pt-2.5">
              <span className="text-xl font-normal tracking-tight">
                {step.label}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
