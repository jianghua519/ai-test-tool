import { Toaster } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import NotFound from "@/pages/NotFound";
import { Route, Switch } from "wouter";
import ErrorBoundary from "./components/ErrorBoundary";
import { ThemeProvider } from "./contexts/ThemeContext";
import Dashboard from "./pages/Dashboard";
import TestCases from "./pages/TestCases";
import TestRuns from "./pages/TestRuns";
import TestCaseEditor from "./pages/TestCaseEditor";
import AutoExplore from "./pages/AutoExplore";

function Router() {
  return (
    <Switch>
      <Route path="/" component={Dashboard} />
      <Route path="/cases" component={TestCases} />
      <Route path="/cases/:id" component={TestCaseEditor} />
      <Route path="/cases/new" component={TestCaseEditor} />
      <Route path="/runs" component={TestRuns} />
      <Route path="/explore" component={AutoExplore} />
      <Route path="/404" component={NotFound} />
      {/* Final fallback route */}
      <Route component={NotFound} />
    </Switch>
  );
}

function App() {
  return (
    <ErrorBoundary>
      <ThemeProvider defaultTheme="system">
        <TooltipProvider>
          <Toaster />
          <Router />
        </TooltipProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
}

export default App;
