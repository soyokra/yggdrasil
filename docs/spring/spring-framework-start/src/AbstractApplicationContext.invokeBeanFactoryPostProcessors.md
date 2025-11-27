## 简述
// 先注册BeanDefinition
执行BeanDefinitionRegistryPostProcessor.postProcessBeanDefinitionRegistry

// 
执行BeanFactoryPostProcessor.postProcessBeanFactory

## 源码分析
```java
final class PostProcessorRegistrationDelegate {


    public static void invokeBeanFactoryPostProcessors(
          ConfigurableListableBeanFactory beanFactory, List<BeanFactoryPostProcessor> beanFactoryPostProcessors) {

       // Invoke BeanDefinitionRegistryPostProcessors first, if any.
       Set<String> processedBeans = new HashSet<>();

       if (beanFactory instanceof BeanDefinitionRegistry) {
           
           // 第一步：先执行外部传入的 beanFactory后置处理器BeanDefinitionRegistryPostProcessor的postProcessBeanDefinitionRegistry方法
          BeanDefinitionRegistry registry = (BeanDefinitionRegistry) beanFactory;
          List<BeanFactoryPostProcessor> regularPostProcessors = new ArrayList<>();
          List<BeanDefinitionRegistryPostProcessor> registryProcessors = new ArrayList<>();

          for (BeanFactoryPostProcessor postProcessor : beanFactoryPostProcessors) {
             if (postProcessor instanceof BeanDefinitionRegistryPostProcessor) {
                BeanDefinitionRegistryPostProcessor registryProcessor =
                      (BeanDefinitionRegistryPostProcessor) postProcessor;
                      
                registryProcessor.postProcessBeanDefinitionRegistry(registry);
                registryProcessors.add(registryProcessor);
             }
             else {
                regularPostProcessors.add(postProcessor);
             }
          }

          // Do not initialize FactoryBeans here: We need to leave all regular beans
          // uninitialized to let the bean factory post-processors apply to them!
          // Separate between BeanDefinitionRegistryPostProcessors that implement
          // PriorityOrdered, Ordered, and the rest.
          List<BeanDefinitionRegistryPostProcessor> currentRegistryProcessors = new ArrayList<>();

          // 第二步：执行继承PriorityOrdered接口的beanFactory后置处理器BeanDefinitionRegistryPostProcessor的postProcessBeanDefinitionRegistry方法
          // 其实就是执行优先级高的，实际上是ConfigurationClassPostProcessor这个处理
          // ConfigurationClassPostProcessor就是注解类的解析，生成和注册BeanDefinition
          // 早期是xml方式，对于新增的注解方式，解决方案是增加 BeanDefinitionRegistryPostProcessor 这个扩展点
          String[] postProcessorNames =
                beanFactory.getBeanNamesForType(BeanDefinitionRegistryPostProcessor.class, true, false);
          for (String ppName : postProcessorNames) {
             if (beanFactory.isTypeMatch(ppName, PriorityOrdered.class)) {
                currentRegistryProcessors.add(beanFactory.getBean(ppName, BeanDefinitionRegistryPostProcessor.class));
                processedBeans.add(ppName);
             }
          }
          sortPostProcessors(currentRegistryProcessors, beanFactory);
          registryProcessors.addAll(currentRegistryProcessors);
          
          // currentRegistryProcessors => ConfigurationClassPostProcessor
          invokeBeanDefinitionRegistryPostProcessors(currentRegistryProcessors, registry);
          
          currentRegistryProcessors.clear();

          // 第三步：执行继承Ordered接口的beanFactory后置处理器BeanDefinitionRegistryPostProcessor的postProcessBeanDefinitionRegistry方法
          // 按顺序执行，默认情况下，并没有这种后置处理器
          postProcessorNames = beanFactory.getBeanNamesForType(BeanDefinitionRegistryPostProcessor.class, true, false);
          for (String ppName : postProcessorNames) {
             if (!processedBeans.contains(ppName) && beanFactory.isTypeMatch(ppName, Ordered.class)) {
                currentRegistryProcessors.add(beanFactory.getBean(ppName, BeanDefinitionRegistryPostProcessor.class));
                processedBeans.add(ppName);
             }
          }
          sortPostProcessors(currentRegistryProcessors, beanFactory);
          registryProcessors.addAll(currentRegistryProcessors);

           // currentRegistryProcessors => empty
          invokeBeanDefinitionRegistryPostProcessors(currentRegistryProcessors, registry);
          currentRegistryProcessors.clear();

          // 第四步：执行所有的beanFactory后置处理器BeanDefinitionRegistryPostProcessor的postProcessBeanDefinitionRegistry方法
          // 这里的while循环是考虑到postProcessBeanDefinitionRegistry方法里可能产生新的beanFactory后置处理器，要全部执行到
          // 使用mybatis的话，就会有MapperScannerConfigurer，扫描xxxMapper为BeanDefinition 
          boolean reiterate = true;
          while (reiterate) {
             reiterate = false;
             postProcessorNames = beanFactory.getBeanNamesForType(BeanDefinitionRegistryPostProcessor.class, true, false);
             for (String ppName : postProcessorNames) {
                if (!processedBeans.contains(ppName)) {
                   currentRegistryProcessors.add(beanFactory.getBean(ppName, BeanDefinitionRegistryPostProcessor.class));
                   processedBeans.add(ppName);
                   reiterate = true;
                }
             }
             sortPostProcessors(currentRegistryProcessors, beanFactory);
             registryProcessors.addAll(currentRegistryProcessors);
             
             // currentRegistryProcessors => MapperScannerConfigurer
             invokeBeanDefinitionRegistryPostProcessors(currentRegistryProcessors, registry);
             currentRegistryProcessors.clear();
          }

          // BeanDefinitionRegistryPostProcessor继承BeanFactoryPostProcessor接口
           // 这里是执行一下BeanDefinitionRegistryPostProcessor类型后置处理的postProcessBeanFactory方法
           //registryProcessors => 
           // CachingMetadataReaderFactoryPostProcessor
           // ConfigurationWarningsPostProcessor
           // ConfigurationClassPostProcessor
           // MapperScannerConfigurer
          invokeBeanFactoryPostProcessors(registryProcessors, beanFactory);
          
          // regularPostProcessors =>
           //PropertySourceOrderingPostProcessor
          invokeBeanFactoryPostProcessors(regularPostProcessors, beanFactory);
       }

       else {
          // Invoke factory processors registered with the context instance.
          invokeBeanFactoryPostProcessors(beanFactoryPostProcessors, beanFactory);
       }

       // 按照 PriorityOrdered -> Ordered -> 普通的顺序执行beanFactory后置处理器BeanFactoryPostProcessor的postProcessBeanFactory方法
       // Do not initialize FactoryBeans here: We need to leave all regular beans
       // uninitialized to let the bean factory post-processors apply to them!
       String[] postProcessorNames =
             beanFactory.getBeanNamesForType(BeanFactoryPostProcessor.class, true, false);

       // Separate between BeanFactoryPostProcessors that implement PriorityOrdered,
       // Ordered, and the rest.
       List<BeanFactoryPostProcessor> priorityOrderedPostProcessors = new ArrayList<>();
       List<String> orderedPostProcessorNames = new ArrayList<>();
       List<String> nonOrderedPostProcessorNames = new ArrayList<>();
       for (String ppName : postProcessorNames) {
          if (processedBeans.contains(ppName)) {
             // skip - already processed in first phase above
          }
          else if (beanFactory.isTypeMatch(ppName, PriorityOrdered.class)) {
             priorityOrderedPostProcessors.add(beanFactory.getBean(ppName, BeanFactoryPostProcessor.class));
          }
          else if (beanFactory.isTypeMatch(ppName, Ordered.class)) {
             orderedPostProcessorNames.add(ppName);
          }
          else {
             nonOrderedPostProcessorNames.add(ppName);
          }
       }

       // First, invoke the BeanFactoryPostProcessors that implement PriorityOrdered.
       sortPostProcessors(priorityOrderedPostProcessors, beanFactory);
       
       // priorityOrderedPostProcessors =>
        // PropertySourcesPlaceholderConfigurer
       invokeBeanFactoryPostProcessors(priorityOrderedPostProcessors, beanFactory);

       // Next, invoke the BeanFactoryPostProcessors that implement Ordered.
       List<BeanFactoryPostProcessor> orderedPostProcessors = new ArrayList<>(orderedPostProcessorNames.size());
       for (String postProcessorName : orderedPostProcessorNames) {
          orderedPostProcessors.add(beanFactory.getBean(postProcessorName, BeanFactoryPostProcessor.class));
       }
       sortPostProcessors(orderedPostProcessors, beanFactory);
       
       // orderedPostProcessors => empty
       invokeBeanFactoryPostProcessors(orderedPostProcessors, beanFactory);

       // Finally, invoke all other BeanFactoryPostProcessors.
       List<BeanFactoryPostProcessor> nonOrderedPostProcessors = new ArrayList<>(nonOrderedPostProcessorNames.size());
       for (String postProcessorName : nonOrderedPostProcessorNames) {
          nonOrderedPostProcessors.add(beanFactory.getBean(postProcessorName, BeanFactoryPostProcessor.class));
       }
       // nonOrderedPostProcessors => 
        // EventListenerMethodProcessor
        // PreserveErrorControllerTargetClassPostProcessor
       invokeBeanFactoryPostProcessors(nonOrderedPostProcessors, beanFactory);

       // Clear cached merged bean definitions since the post-processors might have
       // modified the original metadata, e.g. replacing placeholders in values...
       beanFactory.clearMetadataCache();
    }
}
```


BeanDefinitionRegistryPostProcessor.postProcessBeanDefinitionRegistry实现类
```text
ConfigurationClassPostProcessor
MapperScannerConfigurer
```

BeanFactoryPostProcessor.postProcessBeanFactory实现类
```text
SharedMetadataReaderFactoryContextInitializer$CachingMetadataReaderFactoryPostProcessor
ConfigurationWarningsApplicationContextInitializer$ConfigurationWarningsPostProcessor
ConfigurationClassPostProcessor
MapperScannerConfigurer

ConfigFileApplicationListener$PropertySourceOrderingPostProcessor
PropertySourcePlaceholderConfigurer
EventListenerMethodProcessor
ErrorMvcAutoConfiguration$PreserveErrorControllerTargetClassPostProcessor
```


ConfigurationClassPostProcessor.postProcessBeanDefinitionRegistry方法

扫描包下文件注册beanDefinition

通过 ClassPathBeanDefinitionScanner执行
```java
public class ClassPathBeanDefinitionScanner extends ClassPathScanningCandidateComponentProvider {
    protected Set<BeanDefinitionHolder> doScan(String... basePackages) {
        Assert.notEmpty(basePackages, "At least one base package must be specified");
        Set<BeanDefinitionHolder> beanDefinitions = new LinkedHashSet<>();
        for (String basePackage : basePackages) {
            Set<BeanDefinition> candidates = findCandidateComponents(basePackage);
            for (BeanDefinition candidate : candidates) {
                ScopeMetadata scopeMetadata = this.scopeMetadataResolver.resolveScopeMetadata(candidate);
                candidate.setScope(scopeMetadata.getScopeName());
                String beanName = this.beanNameGenerator.generateBeanName(candidate, this.registry);
                if (candidate instanceof AbstractBeanDefinition) {
                    postProcessBeanDefinition((AbstractBeanDefinition) candidate, beanName);
                }
                if (candidate instanceof AnnotatedBeanDefinition) {
                    AnnotationConfigUtils.processCommonDefinitionAnnotations((AnnotatedBeanDefinition) candidate);
                }
                if (checkCandidate(beanName, candidate)) {
                    BeanDefinitionHolder definitionHolder = new BeanDefinitionHolder(candidate, beanName);
                    definitionHolder =
                            AnnotationConfigUtils.applyScopedProxyMode(scopeMetadata, definitionHolder, this.registry);
                    beanDefinitions.add(definitionHolder);
                    registerBeanDefinition(definitionHolder, this.registry);
                }
            }
        }
        return beanDefinitions;
    }
}
```

调用栈
```text
doScan:273, ClassPathBeanDefinitionScanner (org.springframework.context.annotation)
parse:132, ComponentScanAnnotationParser (org.springframework.context.annotation)
doProcessConfigurationClass:296, ConfigurationClassParser (org.springframework.context.annotation)
processConfigurationClass:250, ConfigurationClassParser (org.springframework.context.annotation)
parse:207, ConfigurationClassParser (org.springframework.context.annotation)
parse:175, ConfigurationClassParser (org.springframework.context.annotation)
processConfigBeanDefinitions:320, ConfigurationClassPostProcessor (org.springframework.context.annotation)
postProcessBeanDefinitionRegistry:237, ConfigurationClassPostProcessor (org.springframework.context.annotation)
invokeBeanDefinitionRegistryPostProcessors:280, PostProcessorRegistrationDelegate (org.springframework.context.support)
invokeBeanFactoryPostProcessors:96, PostProcessorRegistrationDelegate (org.springframework.context.support)
invokeBeanFactoryPostProcessors:707, AbstractApplicationContext (org.springframework.context.support)
refresh:533, AbstractApplicationContext (org.springframework.context.support)
refresh:143, ServletWebServerApplicationContext (org.springframework.boot.web.servlet.context)
refresh:755, SpringApplication (org.springframework.boot)
refresh:747, SpringApplication (org.springframework.boot)
refreshContext:402, SpringApplication (org.springframework.boot)
run:312, SpringApplication (org.springframework.boot)
main:35, StartApplication (com.zuzuche.widget.start)
```

###