import { SignUp } from "@clerk/nextjs";

export default function Page() {
  return (
    <div className="grid place-items-center py-10">
      <SignUp />
    </div>
  );
}
