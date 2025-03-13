// -- lib/walt2_home_screen.dart
import 'package:flutter/material.dart';
import 'api_service.dart';
import 'dart:async';
import 'dart:io';
import 'package:path_provider/path_provider.dart';

class Walt2HomeScreen extends StatefulWidget {
  final String initialMessage;
  final ApiService apiService; // Receive ApiService from main.dart and SplashScreen
  final bool loadStoryOnInit;

  const Walt2HomeScreen({
    super.key,
    required this.initialMessage,
    required this.apiService, // Receive ApiService
    this.loadStoryOnInit = false,
  });

  @override
  _Walt2HomeScreenState createState() => _Walt2HomeScreenState();
}

class _Walt2HomeScreenState extends State<Walt2HomeScreen> {
  String chatOutput = "";
  final TextEditingController _promptController = TextEditingController();
  // late ApiService _apiService; // No need to create ApiService here, using passed one
  bool _isAnalyzing = false;

  @override
  void initState() {
    super.initState();
    // _apiService = widget.apiService; // No need to initialize here, just use the passed one
    setState(() {
      chatOutput = widget.initialMessage;
    });
    if (widget.loadStoryOnInit) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        loadStory();
      });
    }
  }

  // @override // No need to dispose here, ApiService is managed in main.dart
  // void dispose() {
  //   _apiService.closeClient();
  //   super.dispose();
  // }

  ApiService get _apiService => widget.apiService; // Helper to access ApiService easily


  Future<void> _analyzePrompt() async {
    String userInput = _promptController.text.trim();
    if (userInput.isEmpty) return;

    setState(() {
      chatOutput = "Analyzing your prompt...";
      _isAnalyzing = true;
    });

    try {
      final responseMessage = await _apiService.analyzePrompt(userInput);
      setState(() {
        chatOutput = responseMessage;
        _isAnalyzing = false;
      });
      _promptController.clear();
    } catch (e) {
      print("Error in _analyzePrompt: $e");
      setState(() {
        chatOutput = "Error analyzing prompt: $e";
        _isAnalyzing = false;
      });
    }
  }

  // --- File Saving and Loading ---

  Future<String> _getFilePath() async {
    final directory = await getApplicationDocumentsDirectory();
    return '${directory.path}/walt_biography.txt'; // Default file name
  }

  Future<void> saveStory() async {
    setState(() {
      _isAnalyzing = true; // Use analyzing state for saving as well for UI feedback
    });
    try {
      final file = File(await _getFilePath());
      await file.writeAsString(chatOutput);
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("Story saved locally!")),
      );
    } catch (e) {
      print("Error saving story: $e");
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("Error saving story: $e")),
      );
    } finally {
      setState(() {
        _isAnalyzing = false;
      });
    }
  }

  Future<void> loadStory() async {
    setState(() {
      _isAnalyzing = true; // Use analyzing state for loading as well for UI feedback
    });
    try {
      final file = File(await _getFilePath());
      if (await file.exists()) {
        final story = await file.readAsString();
        setState(() {
          chatOutput = story;
        });
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text("Story loaded from local file!")),
        );
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text("No story file found locally.")),
        );
      }
    } catch (e) {
      print("Error loading story: $e");
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("Error loading story: $e")),
      );
    } finally {
      setState(() {
        _isAnalyzing = false;
      });
    }
  }


  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Walt2 Biographer'),
        backgroundColor: Theme.of(context).primaryColor,
        actions: [
          IconButton(
            icon: const Icon(Icons.save),
            tooltip: 'Save Story',
            onPressed: saveStory,
          ),
        ],
      ),
      body: Stack(
        children: [
          SingleChildScrollView(
            child: Padding(
              padding: const EdgeInsets.all(20.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.center,
                children: [
                  const Text(
                    "Let’s write your story together!",
                    style: TextStyle(
                      fontStyle: FontStyle.italic,
                      color: Color(0xFF777777),
                    ),
                  ),
                  const SizedBox(height: 20),
                  Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Expanded(
                        child: Container(
                          padding: const EdgeInsets.all(20),
                          decoration: BoxDecoration(
                            border: Border.all(color: const Color(0xFFEEEEEE)),
                            borderRadius: BorderRadius.circular(12),
                            color: Colors.white,
                          ),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Text(
                                "Walt",
                                style: TextStyle(
                                  color: Color(0xFF007AFF),
                                  fontWeight: FontWeight.w500,
                                  fontSize: 20,
                                ),
                              ),
                              const SizedBox(height: 10),
                              SizedBox(
                                height: 400,
                                child: SingleChildScrollView(
                                  child: Text(
                                    chatOutput,
                                    style: const TextStyle(fontSize: 16),
                                  ),
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                      const SizedBox(width: 20),
                      Expanded(
                        child: Container(
                          padding: const EdgeInsets.all(20),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Text(
                                "Your Story",
                                style: TextStyle(
                                  color: Color(0xFF007AFF),
                                  fontWeight: FontWeight.w500,
                                  fontSize: 20,
                                ),
                              ),
                              const SizedBox(height: 10),
                              TextField(
                                controller: _promptController,
                                maxLines: 8,
                                decoration: const InputDecoration(
                                  border: OutlineInputBorder(),
                                  hintText: "Tell Walt about your life...",
                                ),
                              ),
                              const SizedBox(height: 10),
                              ElevatedButton(
                                onPressed: _analyzePrompt,
                                style: ElevatedButton.styleFrom(
                                  backgroundColor: Colors.yellow,
                                  foregroundColor: Colors.grey,
                                  minimumSize: const Size(double.infinity, 50),
                                ),
                                child: const Text("Submit"),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
          if (_isAnalyzing)
            Positioned.fill(
              child: Container(
                color: Colors.black.withOpacity(0.5),
                child: const Center(
                  child: CircularProgressIndicator(color: Colors.white),
                ),
              ),
            ),
        ],
      ),
    );
  }
}
// -- lib/walt2_home_screen.dart
