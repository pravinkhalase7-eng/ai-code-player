import { LearnClient } from "@/components/player/LearnClient";

export default async function LearnPage({
  params,
}: {
  params: Promise<{ lessonId: string }>;
}) {
  const { lessonId } = await params;
  return (
    <div className="mx-auto max-w-7xl overflow-x-hidden px-3 py-4 sm:px-4 sm:py-6 md:px-8">
      <LearnClient lessonId={lessonId} />
    </div>
  );
}
